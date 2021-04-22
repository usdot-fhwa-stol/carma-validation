# extracting the roadway_objects topic directly from the rosbag
# for a cleaner file than the default csv extraction

import rosbag
import pandas as pd 

# downloaded bag locally first
# trying to use the bag in D:/ was unsuccessful, just started eating up memory
bag = rosbag.Bag("C:/Users/ian.berg/Documents/from-s3-temp/LS_SPLMS_v3.5.3_r18_down-selected.bag")

obj_cols = ["rosbagTimestamp","object_id","pos_x","pos_y","pos_z","orient_x","orient_y","orient_z","orient_w","speed","size_x","size_y","size_z","confidence","type","cv_type","lanelet_id","cross_track","down_track"]
df_all_obj = pd.DataFrame(columns = obj_cols)
for topic, msg, t in bag.read_messages(topics="/environment/roadway_objects"):
    # the spec for /environment/roadway_objects is cav_mgs/RoadwayObstacleList
    # https://github.com/usdot-fhwa-stol/carma-msgs/blob/develop/cav_msgs/msg/RoadwayObstacleList.msg
    # used this and the specs of the messages nested within to define the columns
    df_msg = pd.DataFrame(columns= obj_cols)
    for item in msg.roadway_obstacles:
        obj = {}
        obj["rosbagTimestamp"] = int(str(t))
        obj["object_id"] = item.object.id
        obj["pos_x"] = item.object.pose.pose.position.x
        obj["pos_y"] = item.object.pose.pose.position.y
        obj["pos_z"] = item.object.pose.pose.position.z
        obj["orient_x"] = item.object.pose.pose.orientation.x
        obj["orient_y"] = item.object.pose.pose.orientation.y
        obj["orient_z"] = item.object.pose.pose.orientation.z
        obj["orient_w"] = item.object.pose.pose.orientation.w
        obj["speed"] = item.object.velocity.twist.linear.x # should check that y and z are always empty, looks to be true
        obj["size_x"] = item.object.size.x
        obj["size_y"] = item.object.size.y
        obj["size_z"] = item.object.size.z
        obj["confidence"] = item.object.confidence
        obj["type"] = item.object.object_type
        obj["cv_type"] = item.connected_vehicle_type.type
        obj["lanelet_id"] = item.lanelet_id
        obj["cross_track"] = item.cross_track
        obj["down_track"] = item.down_track
        df_msg = df_msg.append(obj, ignore_index =True)
    df_msg = df_msg.drop_duplicates() # in sample data, each message contains many duplicate copies of the same object
    df_all_obj = df_all_obj.append(df_msg, ignore_index = True)

df_all_obj.to_csv("environment_roadway_objects.csv")