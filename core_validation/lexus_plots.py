
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
run = "LS_SMPL_v3.5.1_r11"

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

plt.show()