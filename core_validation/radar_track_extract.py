# extracting the radar_tracks topic directly from the rosbag
# for a cleaner file than the default csv extraction

import rosbag
import pandas as pd

# downloaded bag locally (to the EC2 instance) first
# trying to use the bag in D:/ was unsuccessful, just started eating up memory
run = "P_SPLMS_v3.5.3_r15"
bag = rosbag.Bag("C:/Users/ian.berg/Documents/from-s3-temp/{}_down-selected.bag".format(run))

obj_cols = ["rosbagTimestamp","track_id","pos","vel_x","vel_y", "accel_x"]
df_all_obj = pd.DataFrame(columns = obj_cols)
for topic, msg, t in bag.read_messages(topics="/radar_fc/as_tx/radar_tracks"):
    # the spec is radar_msgs/RadarTrackArray
    # http://docs.ros.org/en/melodic/api/radar_msgs/html/msg/RadarTrackArray.html
    df_msg = pd.DataFrame(columns= obj_cols)
    for item in msg.tracks:
        obj = {}
        obj["rosbagTimestamp"] = int(str(t))
        obj["track_id"] = item.track_id
        obj["pos"] = item.track_shape.points # lazy
        obj["vel_x"] = item.linear_velocity.x
        obj["vel_y"] = item.linear_velocity.y
        obj["accel_x"] = item.linear_acceleration.z
        df_msg = df_msg.append(obj, ignore_index =True)
    #df_msg = df_msg.drop_duplicates() # in sample data, each message contains many duplicate copies of the same object
    df_all_obj = df_all_obj.append(df_msg, ignore_index = True)

df_all_obj.to_csv("{}_radar_fc_as_tx_radar_tracks.csv".format(run), index=False)