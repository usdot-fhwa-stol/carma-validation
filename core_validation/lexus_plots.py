# setting up 
import boto3
import pandas as pd
import os
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString

# helper from misc folder
def csv_loc_from_name(run_name):
    # TODO: generalize or pass as input
    csv_loc = "csvfiles/Core_Validation_Testing/Facility_Summit_Point/"
    
    veh = run_name.split("_")[0]
    run_no = run_name.split("_")[-1]

    if veh == "P":
        csv_loc = csv_loc + "Vehicle_Black_Pacifica/"
    elif veh == "LS":
        csv_loc = csv_loc + "Vehicle_Silver_Lexus/"
    elif veh == "F":
        csv_loc = csv_loc + "Vehicle_White_Ford/"
    
    # assume with more runs will need to stop hardcoding dates
    # TODO: generalize or pass as input
    csv_loc = csv_loc + "20210318/{}_down-selected/".format(run_no)
    return csv_loc

# cleaning up loading the topics
def load_topic(bucket, run, csv_name):
    file_name = csv_loc_from_name(run) + csv_name
    obj = s3_client.get_object(Bucket=bucket, Key=file_name)
    df = pd.read_csv(obj['Body'])
    # get elapsed time in seconds as a field -- should revise to improve precision
    # TODO: refine by picking a topic and setting the run-wide start timestamp to use 
    #  instead of min(df.rosbagTimestamp) for each run's start
    df['elapsed_time'] = (df.rosbagTimestamp-min(df.rosbagTimestamp))/1000000000.0
    # TODO: elapsed distance
    return df


s3_client = boto3.client('s3')
bucket = 'preprocessed-carma-core-validation'
run = "LS_SMPL_v3.5.1_r5"

# load necessary topics
topic_cmd = "hardware_interface_vehicle_cmd.csv"
topic_spd = "hardware_interface_pacmod_parsed_tx_vehicle_speed_rpt.csv"
topic_imu = "hardware_interface_imu_raw.csv"
topic_state = "guidance_state.csv"
topic_pose = "localization_current_pose.csv"
topic_steer = "hardware_interface_pacmod_parsed_tx_steer_rpt.csv"
topic_throttle = "hardware_interface_pacmod_parsed_tx_accel_rpt.csv"
topic_brake = "hardware_interface_pacmod_parsed_tx_brake_rpt.csv"

df_cmd = load_topic(bucket, run, topic_cmd)
df_spd = load_topic(bucket, run, topic_spd)
df_imu = load_topic(bucket, run, topic_imu)
df_state = load_topic(bucket, run, topic_state)
df_pose = load_topic(bucket, run, topic_pose)
df_steer = load_topic(bucket, run, topic_steer)
df_throttle = load_topic(bucket, run, topic_throttle)
df_brake = load_topic(bucket, run, topic_brake)


# set up scatterplot default symbol to be small
plt.rcParams['scatter.marker'] = '.'

# get state of CARMA system (4=ENGAGED) 
plt.figure(1)
plt.plot(df_state.elapsed_time, df_state.state, label="state")
plt.xlabel("Time (elapsed seconds)")
plt.legend()
plt.title(run + ",\n" + topic_state)

# speed, commanded vs actual
plt.figure(2)
plt.scatter(df_cmd.elapsed_time, df_cmd.linear_velocity, label = "commanded")
plt.scatter(df_spd.elapsed_time, df_spd.vehicle_speed, label = "actual")
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Speed (m/s)")
plt.legend()
plt.title(run + ",\n" + topic_cmd + "\nand " + topic_spd)

# longitudinal accel, commanded vs actual
# vehicle_cmd has two different acceleration command values, but neither seem to make sense
plt.figure(3)
# plt.scatter(df_cmd.elapsed_time, df_cmd.accel, label = "commanded") # this is always all 0s
plt.scatter(df_cmd.elapsed_time, df_cmd.linear_acceleration, label = "commanded")
plt.scatter(df_imu.elapsed_time, df_imu["y.2"], label = "actual")
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Acceleration (m/s^2)")
plt.legend()
plt.title(run + ",\n" + topic_cmd + "\nand " + topic_imu)

# crosstrack distance from vehicle centroid to center dashed line 
df_cl = pd.read_csv("misc/sp_loop_centerline.csv")
df_cl = df_cl.set_index(df_cl.way_id * 10000 + df_cl.way_pos) #ensure correct ordering
## convert points to a linestring
## based on https://stackoverflow.com/questions/51071365/convert-points-to-lines-geopandas
points_list = [Point(xy) for xy in zip(df_cl.X, df_cl.Y)]
centerline = LineString(points_list)
## get distance to centerline
gdf_pose = gpd.GeoDataFrame(df_pose, geometry=gpd.points_from_xy(df_pose.x,df_pose.y))
gdf_pose["dist_to_cl"] = gdf_pose.geometry.distance(centerline)
## setup figure
plt.figure(4)
plt.scatter(gdf_pose.elapsed_time, gdf_pose.dist_to_cl) 
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Crosstrack distance to road centerline (m)")
plt.ylim(0,3.4) # Tim's assumption: lane width is 3.4m = 11ft
#plt.legend()
plt.title(run + ",\n" + topic_pose)

# throttle pct actual vs commanded
plt.figure(5)
plt.scatter(df_throttle.elapsed_time, df_throttle.command, label="input")
plt.scatter(df_throttle.elapsed_time, df_throttle.output, label="output")
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Throttle (percent))")
plt.legend()
plt.title(run + ",\n" + topic_throttle)

# steering angle actual vs commanded
plt.figure(6)
plt.scatter(df_steer.elapsed_time, df_steer.command, label="input")
plt.scatter(df_steer.elapsed_time, df_steer.output, label="output")
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Steering angle (rad)")
plt.legend()
plt.title(run + ",\n" + topic_steer)

# brake pct actual vs commanded
plt.figure(7)
plt.scatter(df_brake.elapsed_time, df_brake.command, label="input")
plt.scatter(df_brake.elapsed_time, df_brake.output, label="output")
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Braking (percent)")
plt.legend()
plt.title(run + ",\n" + topic_brake)

plt.show()