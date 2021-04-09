# setting up 
import boto3
import numpy as np
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
    return df


# get elapsed time in seconds as a field 
def calc_elapsed_time(dfs):
    min_timestamp = np.inf
    for df in dfs.values():
        min_timestamp = min(min_timestamp, min(df['rosbagTimestamp']))
    
    for df in dfs.values():
        df['elapsed_time'] = (df['rosbagTimestamp'] - min_timestamp)/1000000000.0
    
    # TODO: elapsed distance
    return dfs


def rle(inarray):
    """ run length encoding. Partial credit to R rle function.
        Multi datatype arrays catered for including non Numpy
        returns: tuple (runlengths, startpositions, values) """
    ia = np.asarray(inarray)  # force numpy
    n = len(ia)
    if n == 0:
        return (None, None, None)
    else:
        y = np.array(ia[1:] != ia[:-1])  # pairwise unequal (string safe)
        i = np.append(np.where(y), n - 1)  # must include last element posi
        z = np.diff(np.append(-1, i))  # run lengths
        p = np.cumsum(np.append(0, z))[:-1]  # positions
        return (z, p, ia[i])

def finish_plot(plot_title):
    plt.xlabel("Time (elapsed seconds)")
    plt.xlim(max(0,carma_start_time-10),carma_end_time+10)
    left, right = plt.xlim()
    plt.axvspan(left, carma_start_time, color='lightblue', alpha=0.5)
    plt.axvspan(carma_end_time, right, color='lightblue', alpha=0.5)
    plt.legend()
    plt.title(plot_title + "\n" + run)


s3_client = boto3.client('s3')
bucket = 'preprocessed-carma-core-validation'
run = "P_SPLMS_v3.5.1_r14"

# load necessary topics
topics = {}
topics['cmd'] = "hardware_interface_vehicle_cmd.csv"
topics['spd'] = "hardware_interface_misc_report.csv"
topics['imu'] = "hardware_interface_imu_data_raw.csv"
topics['state'] = "guidance_state.csv"
topics['pose'] = "localization_current_pose.csv"
topics['steer'] = "hardware_interface_steering_report.csv"
topics['steer_cmd'] = "hardware_interface_steering_cmd.csv"
topics['throttle'] = "hardware_interface_accelerator_pedal_report.csv"
topics['throttle_cmd'] = "hardware_interface_accelerator_pedal_cmd.csv"
topics['brake'] = "hardware_interface_brake_report.csv"
topics['brake_cmd'] = "hardware_interface_brake_cmd.csv"


dfs = {k: load_topic(bucket, run, v) for k, v in topics.items()}
dfs = calc_elapsed_time(dfs)

# set up scatterplot default symbol to be small
plt.rcParams['scatter.marker'] = '.'
# find longest stretch of CARMA state = 4 during run
z, p, ia = rle(dfs['state'].state == 4)
carma_start_ind = p[z == max(z[ia])][0]
carma_end_ind = carma_start_ind + z[z == max(z[ia])][0] - 1
carma_start_time = dfs['state'].loc[carma_start_ind, 'elapsed_time']
carma_end_time = dfs['state'].loc[carma_end_ind, 'elapsed_time']

# get state of CARMA system (4=ENGAGED) 
plt.figure(1)
plt.plot(dfs['state'].elapsed_time, dfs['state'].state, label="state")
finish_plot("CARMA System state")

# speed, commanded vs actual
plt.figure(2)
plt.scatter(dfs['cmd'].elapsed_time, dfs['cmd'].linear_velocity, label = "commanded")
plt.scatter(dfs['spd'].elapsed_time, dfs['spd'].vehicle_speed, label = "actual")
plt.ylabel("Speed (m/s)")
finish_plot("Speed (commanded vs. actual)")

# longitudinal accel, commanded vs actual
# vehicle_cmd has two different acceleration command values, but neither seem to make sense
plt.figure(3)
# plt.scatter(df_cmd.elapsed_time, df_cmd.accel, label = "commanded") # this is always all 0s
plt.scatter(dfs['cmd'].elapsed_time, dfs['cmd'].linear_acceleration, label = "commanded")
plt.scatter(dfs['imu'].elapsed_time, dfs['imu']['y.2'], label = "actual")
plt.ylabel("Acceleration (m/s^2)")
finish_plot("Acceleration (commanded vs. actual)")

# crosstrack distance from vehicle centroid to center dashed line 
df_cl = pd.read_csv("misc/sp_loop_centerline.csv")
df_cl = df_cl.set_index(df_cl.way_id * 10000 + df_cl.way_pos) #ensure correct ordering
## convert points to a linestring
## based on https://stackoverflow.com/questions/51071365/convert-points-to-lines-geopandas
points_list = [Point(xy) for xy in zip(df_cl.X, df_cl.Y)]
centerline = LineString(points_list)
## get distance to centerline
gdf_pose = gpd.GeoDataFrame(dfs['pose'], geometry=gpd.points_from_xy(dfs['pose'].x,dfs['pose'].y))
gdf_pose["dist_to_cl"] = gdf_pose.geometry.distance(centerline)
## setup figure
plt.figure(4)
plt.scatter(gdf_pose.elapsed_time, gdf_pose.dist_to_cl) 
plt.ylabel("Crosstrack distance to road centerline (m)")
plt.ylim(0,3.4) # Tim's assumption: lane width is 3.4m = 11ft
finish_plot("Distance: vehicle centroid to road centerline")

# throttle pct actual vs commanded
plt.figure(5)
plt.scatter(dfs['throttle_cmd'].elapsed_time, dfs['throttle_cmd'].pedal_cmd, label="commanded")
plt.scatter(dfs['throttle'].elapsed_time, dfs['throttle'].pedal_output, label="actual")
plt.ylabel("Throttle (percent))")
finish_plot("Throttle (commanded vs. actual)")


# steering angle actual vs commanded
plt.figure(6)
plt.scatter(dfs['steer_cmd'].elapsed_time, dfs['steer_cmd'].angle_cmd, label="commanded")
plt.scatter(dfs['steer'].elapsed_time, dfs['steer'].steering_wheel_angle, label="actual")
plt.ylabel("Steering angle (rad)")
finish_plot("Steering (commanded vs. actual)")

# brake pct actual vs commanded
plt.figure(7)
plt.scatter(dfs['brake_cmd'].elapsed_time, dfs['brake_cmd'].pedal_cmd, label="commanded")
plt.scatter(dfs['brake'].elapsed_time, dfs['brake'].pedal_output, label="actual")
plt.ylabel("Braking (percent)")
finish_plot("Braking (commanded vs. actual)")

fig, ax1 = plt.subplots()

color11 = 'tab:red'
color12 = 'tab:orange'
ax1.set_xlabel('Time (elapsed seconds)')
ax1.set_ylabel('Speed (m/s)', color=color11)
ax1.scatter(dfs['cmd'].elapsed_time, dfs['cmd'].linear_velocity, label = "commanded_spd", color=color11, s=10)
ax1.scatter(dfs['spd'].elapsed_time, dfs['spd'].vehicle_speed, label = "actual_spd", color=color12, s=10)
ax1.tick_params(axis='y', labelcolor=color11)

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color21 = 'tab:blue'
color22 = 'tab:green'
ax2.set_ylabel('Acceleration (m/s^2)', color=color21)  # we already handled the x-label with ax1
ax2.scatter(dfs['cmd'].elapsed_time, dfs['cmd'].linear_acceleration, label = "commanded_accel", color=color21, s=10)
ax2.scatter(dfs['imu'].elapsed_time, dfs['imu']["y.2"], label = "actual_accel", color=color22, s=10)
plt.ylim(-5,5) # reasonable acceleration limits
ax2.tick_params(axis='y', labelcolor=color21)
plt.legend()

fig.tight_layout()  # otherwise the right y-label is slightly clipped

plt.show()