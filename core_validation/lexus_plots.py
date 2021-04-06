
# helper from misc folder
def csv_loc_from_name(run_name):
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
    csv_loc = csv_loc + "20210318/{}_down-selected/".format(run_no)
    return csv_loc

# setting up 
import boto3
import pandas as pd
import os
import matplotlib.pyplot as plt

s3_client = boto3.client('s3')
bucket = 'preprocessed-carma-core-validation'
run = "LS_SMPL_v3.5.1_r5"

# load necessary topics
file_name = csv_loc_from_name(run) + "hardware_interface_vehicle_cmd.csv"
obj = s3_client.get_object(Bucket=bucket, Key=file_name)
df_cmd = pd.read_csv(obj['Body'])

file_name = csv_loc_from_name(run) + "hardware_interface_pacmod_parsed_tx_vehicle_speed_rpt.csv"
obj = s3_client.get_object(Bucket=bucket, Key=file_name)
df_spd = pd.read_csv(obj['Body'])

file_name = csv_loc_from_name(run) + "hardware_interface_imu_raw.csv"
obj = s3_client.get_object(Bucket=bucket, Key=file_name)
df_imu = pd.read_csv(obj['Body'])

file_name = csv_loc_from_name(run) + "guidance_state.csv"
obj = s3_client.get_object(Bucket=bucket, Key=file_name)
df_state = pd.read_csv(obj['Body'])

file_name = csv_loc_from_name(run) + "localization_current_pose.csv"
obj = s3_client.get_object(Bucket=bucket, Key=file_name)
df_pose = pd.read_csv(obj['Body'])

# get state of CARMA system (4=ENGAGED) 
plt.figure(1)
plt.plot((df_state.rosbagTimestamp-min(df_state.rosbagTimestamp))/1000000000, df_state.state, label="state")
plt.legend()
plt.title(run)

# speed, commanded vs actual
plt.figure(2)
plt.scatter((df_cmd.rosbagTimestamp-min(df_cmd.rosbagTimestamp))/1000000000, df_cmd.linear_velocity, marker = ".", label = "commanded")
plt.scatter((df_spd.rosbagTimestamp-min(df_spd.rosbagTimestamp))/1000000000, df_spd.vehicle_speed, marker = ".",  label = "actual")
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Speed (m/s)")
plt.legend()
plt.title(run)

# accel, commanded vs actual
# vehicle_cmd has two different acceleration command values, but neither seem to make sense
plt.figure(3)
plt.scatter((df_cmd.rosbagTimestamp-min(df_cmd.rosbagTimestamp))/1000000000, df_cmd.accel, marker = ".", label = "commanded")
plt.scatter((df_cmd.rosbagTimestamp-min(df_cmd.rosbagTimestamp))/1000000000, df_cmd.linear_acceleration, marker = ".", label = "commanded2")
plt.scatter((df_imu.rosbagTimestamp-min(df_imu.rosbagTimestamp))/1000000000, df_imu["x.2"], marker = ".", label = "actual")
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Acceleration (m/s^2)")
plt.legend()
plt.title(run)

# alternate option using /hardware_interface/pacmod/parsed_tx/accel_rpt?
# plt.figure(3)
# plt.scatter((df2.rosbagTimestamp-min(df2.rosbagTimestamp))/1000000000, df2.command,marker = ".", label="input")
# plt.scatter((df2.rosbagTimestamp-min(df2.rosbagTimestamp))/1000000000, df2.output,marker = ".", label="output")
# plt.xlabel("Time (elapsed seconds)")
# plt.ylabel("Throttle (0-100%)")
# plt.legend()
# plt.title(run)

# crosstrack distance from vehicle centroid to center dashed line 
df_cl = pd.read_csv("misc/sp_loop_centerline.csv")
df_cl = df_cl.set_index(df_cl.way_id * 10000 + df_cl.way_pos) #ensure correct ordering
import geopandas as gpd
from shapely.geometry import Point, LineString
## convert points to a linestring
## based on https://stackoverflow.com/questions/51071365/convert-points-to-lines-geopandas
points_list = [Point(xy) for xy in zip(df_cl.X, df_cl.Y)]
centerline = LineString(points_list)
## get distance to centerline
gdf_pose = gpd.GeoDataFrame(df_pose, geometry=gpd.points_from_xy(df_pose.x,df_pose.y))
gdf_pose["dist_to_cl"] = gdf_pose.geometry.distance(centerline)
## setup figure
plt.figure(4)
plt.scatter((gdf_pose.rosbagTimestamp-min(gdf_pose.rosbagTimestamp))/1000000000, gdf_pose.dist_to_cl) 
plt.xlabel("Time (elapsed seconds)")
plt.ylabel("Crosstrack distance to road centerline (m)")
plt.ylim(0,3.4) # Tim's assumption: lane width is 3.4m = 11ft
#plt.legend()
plt.title(run)
plt.show()