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


def finish_plot(plot_title, save_figs):
    plt.xlabel("Time (elapsed seconds)")
    plt.xlim(max(0,carma_start_time-10),carma_end_time+10)
    left, right = plt.xlim()
    plt.axvspan(left, carma_start_time, color='lightblue', alpha=0.5)
    plt.axvspan(carma_end_time, right, color='lightblue', alpha=0.5)
    plt.legend()
    plt.grid(True)
    plt.title(plot_title + "\n" + run)
    if save_figs:
        plt.savefig("C:/Users/Public/Documents/outplots/{}/Figure_{}.png".format(run, plt.gcf().number))


s3_client = boto3.client('s3')
bucket = 'preprocessed-carma-core-validation'
# run = "LS_SMPL_v3.5.1_r9"
# run = "F_SPLMS_v3.5.1_r11"
run = "P_SPLMS_v3.5.1_r8"
veh = run.split("_")[0]
save_figs = False
if save_figs:
    if not os.path.exists("C:/Users/Public/Documents/outplots/{}".format(run)):
        os.mkdir("C:/Users/Public/Documents/outplots/{}".format(run))

# load necessary topics
topics = {}
topics['state'] = "guidance_state.csv"
topics['cmd'] = "hardware_interface_vehicle_cmd.csv"
topics['corrimudata'] = "hardware_interface_corrimudata.csv"
topics['pose'] = "localization_current_pose.csv"

fields = {}
fields['state'] = 'state'
fields['spd_cmd'] = 'linear_velocity'
fields['accel_cmd'] = 'linear_acceleration'
fields['yaw_nov'] = 'yaw_rate'
fields['lat_accel_nov'] = 'lateral_acceleration'
fields['long_accel_nov'] = 'longitudinal_acceleration'
fields['vert_accel_nov'] = 'vertical_acceleration'
fields['pose_x'] = 'x'
fields['pose_y'] = 'y'

if veh == "P":
    topics['spd'] = "hardware_interface_misc_report.csv"
    topics['imu'] = "hardware_interface_imu_data_raw.csv"
    topics['steer'] = "hardware_interface_steering_report.csv"
    topics['steer_cmd'] = "hardware_interface_steering_cmd.csv"
    topics['throttle'] = "hardware_interface_accelerator_pedal_report.csv"
    topics['throttle_cmd'] = "hardware_interface_accelerator_pedal_cmd.csv"
    topics['brake'] = "hardware_interface_brake_report.csv"
    topics['brake_cmd'] = "hardware_interface_brake_cmd.csv"

    fields['spd'] = 'vehicle_speed'
    fields['lat_accel'] = 'x.2'
    fields['long_accel'] = 'y.2'
    fields['steer_cmd'] = 'angle_cmd'
    fields['steer_act'] = 'steering_wheel_angle'
    fields['throttle_cmd'] = 'pedal_cmd'
    fields['throttle_act'] = 'pedal_output'
    fields['brake_cmd'] = 'pedal_cmd'
    fields['brake_act'] = 'pedal_output'
elif veh == "LS":
    topics['spd'] = "hardware_interface_pacmod_parsed_tx_vehicle_speed_rpt.csv"
    topics['imu'] = "hardware_interface_imu_raw.csv"
    topics['steer'] = "hardware_interface_pacmod_parsed_tx_steer_rpt.csv"
    topics['steer_cmd'] = "hardware_interface_pacmod_as_rx_steer_cmd.csv"
    topics['throttle'] = "hardware_interface_pacmod_parsed_tx_accel_rpt.csv"
    topics['throttle_cmd'] = "hardware_interface_pacmod_as_rx_accel_cmd.csv"
    topics['brake'] = "hardware_interface_pacmod_parsed_tx_brake_rpt.csv"
    topics['brake_cmd'] = "hardware_interface_pacmod_as_rx_brake_cmd.csv"

    fields['spd'] = 'vehicle_speed'
    fields['lat_accel'] = 'x.2'
    fields['long_accel'] = 'y.2'
    fields['steer_cmd'] = 'command'
    fields['steer_act'] = 'output'
    fields['throttle_cmd'] = 'command'
    fields['throttle_act'] = 'output'
    fields['brake_cmd'] = 'command'
    fields['brake_act'] = 'output'
elif veh == "F":
    topics['spd'] = "hardware_interface_ds_fusion_steering_report.csv"
    topics['imu'] = "hardware_interface_ds_fusion_imu_data_raw.csv"
    topics['steer'] = "hardware_interface_ds_fusion_steering_report.csv"
    topics['steer_cmd'] = "hardware_interface_ds_fusion_steering_cmd.csv"
    topics['throttle'] = "hardware_interface_ds_fusion_throttle_report.csv"
    topics['throttle_cmd'] = "hardware_interface_ds_fusion_throttle_cmd.csv"
    topics['brake'] = "hardware_interface_ds_fusion_brake_report.csv"
    topics['brake_cmd'] = "hardware_interface_ds_fusion_brake_cmd.csv"

    fields['spd'] = 'speed'
    fields['lat_accel'] = 'x.2'
    fields['long_accel'] = 'y.2'
    fields['steer_cmd'] = 'steering_wheel_angle_cmd'
    fields['steer_act'] = 'steering_wheel_angle'
    fields['throttle_cmd'] = 'pedal_cmd'
    fields['throttle_act'] = 'pedal_output'
    fields['brake_cmd'] = 'pedal_cmd'
    fields['brake_act'] = 'pedal_output'
else:
    print("Invalid vehicle specified in run.")
    exit


dfs = {k: load_topic(bucket, run, v) for k, v in topics.items()}
dfs = calc_elapsed_time(dfs)

# set up scatterplot default symbol to be small
# and figure size (make larger than default)
plt.rcParams['scatter.marker'] = '.'
plt.rcParams['lines.markersize'] = 3
plt.rcParams['figure.figsize'] = [8, 6]

# find longest stretch of CARMA state = 4 during run
z, p, ia = rle(dfs['state'].state == 4)
carma_start_ind = p[z == max(z[ia])][0]
carma_end_ind = carma_start_ind + z[z == max(z[ia])][0] - 1
carma_start_time = dfs['state'].loc[carma_start_ind, 'elapsed_time']
carma_end_time = dfs['state'].loc[carma_end_ind, 'elapsed_time']

# get state of CARMA system (4=ENGAGED) 
plt.figure(0)
plt.scatter(dfs['state'].elapsed_time, dfs['state'][fields['state']], label="state")
finish_plot("CARMA System state", False)

# speed, commanded vs actual
plt.figure(1)
plt.scatter(dfs['cmd'].elapsed_time, dfs['cmd'][fields['spd_cmd']], label = "commanded")
plt.scatter(dfs['spd'].elapsed_time, dfs['spd'][fields['spd']], label = "actual")
plt.ylabel("Speed (m/s)")
finish_plot("Speed (commanded vs. actual)", save_figs)

# longitudinal accel, commanded vs actual
# vehicle_cmd has two different acceleration command values, but neither seem to make sense
# TODO: vehicle_cmd seems to only contain a "linear acceleration" command - how does this relate to accel x, y, z?
plt.figure(2)
# plt.scatter(df_cmd.elapsed_time, df_cmd.accel, label = "commanded") # this is always all 0s
plt.scatter(dfs['cmd'].elapsed_time, dfs['cmd'][fields['accel_cmd']], label = "commanded")
plt.scatter(dfs['imu'].elapsed_time, dfs['imu'][fields['long_accel']], label = "actual")
plt.ylabel("Acceleration (m/s^2)")
plt.ylim(-5,5)
plt.figtext(0.99, 0.01,
 '{} of {} commands outside plot range; min {:.2f}; max {:.2f}'.format(
     len(dfs['cmd'].loc[abs(dfs['cmd'][fields['accel_cmd']]) > 5, fields['accel_cmd']]),
     len(dfs['cmd'][fields['accel_cmd']]),
     min(dfs['cmd'][fields['accel_cmd']]),
     max(dfs['cmd'][fields['accel_cmd']])
 ), horizontalalignment='right')
finish_plot("Acceleration (commanded vs. actual)", save_figs)

# crosstrack distance from vehicle centroid to center dashed line 
df_cl = pd.read_csv("misc/sp_loop_centerline.csv")
df_cl = df_cl.set_index(df_cl.way_id * 10000 + df_cl.way_pos) #ensure correct ordering
## convert points to a linestring
## based on https://stackoverflow.com/questions/51071365/convert-points-to-lines-geopandas
points_list = [Point(xy) for xy in zip(df_cl.X, df_cl.Y)]
centerline = LineString(points_list)
## get distance to centerline
gdf_pose = gpd.GeoDataFrame(dfs['pose'], geometry=gpd.points_from_xy(dfs['pose'][fields['pose_x']],dfs['pose'][fields['pose_y']]))
gdf_pose['dist_to_cl'] = gdf_pose.geometry.distance(centerline)
## setup figure
plt.figure(3)
plt.scatter(gdf_pose.elapsed_time, gdf_pose.dist_to_cl, label="distance") 
plt.ylabel("Crosstrack distance to road centerline (m)")
plt.ylim(0,3.4) # Tim's assumption: lane width is 3.4m = 11ft
finish_plot("Distance: vehicle centroid to road centerline", save_figs)

# throttle pct actual vs commanded
plt.figure(4)
plt.scatter(dfs['throttle_cmd'].elapsed_time, dfs['throttle_cmd'][fields['throttle_cmd']], label="commanded")
plt.scatter(dfs['throttle'].elapsed_time, dfs['throttle'][fields['throttle_act']], label="actual")
if veh == "F":
    plt.ylabel("Throttle (range 0.15 to 0.80)")
else:
    plt.ylabel("Throttle (percent))")
finish_plot("Throttle (commanded vs. actual)", save_figs)

# steering angle actual vs commanded
plt.figure(5)
plt.scatter(dfs['steer_cmd'].elapsed_time, dfs['steer_cmd'][fields['steer_cmd']], label="commanded")
plt.scatter(dfs['steer'].elapsed_time, dfs['steer'][fields['steer_act']], label="actual")
plt.ylabel("Steering angle (rad)")
finish_plot("Steering (commanded vs. actual)", save_figs)

# brake pct actual vs commanded
plt.figure(6)
plt.scatter(dfs['brake_cmd'].elapsed_time, dfs['brake_cmd'][fields['brake_cmd']], label="commanded")
plt.scatter(dfs['brake'].elapsed_time, dfs['brake'][fields['brake_act']], label="actual")
if veh == "F":
    plt.ylabel("Braking (range 0.15 to 0.80)")
else:
    plt.ylabel("Braking (percent)")
finish_plot("Braking (commanded vs. actual)", save_figs)
'''
dfs['corrimudata']['novatel_time'] = dfs['corrimudata'].secs + dfs['corrimudata'].nsecs/1000000000.0
# calculate yaw rate, lateral acceleration, longitundinal acceleration, vertical acceleration from Novatel IMU
imu_diff = dfs['corrimudata'][['novatel_time', fields['yaw_nov'], fields['lat_accel_nov'], fields['long_accel_nov'], fields['vert_accel_nov']]].diff()
imu_diff['yaw'] = imu_diff[fields['yaw_nov']] / imu_diff['novatel_time']
imu_diff['lat_accel'] = imu_diff[fields['lat_accel_nov']] / imu_diff['novatel_time']
imu_diff['long_accel'] = imu_diff[fields['long_accel_nov']] / imu_diff['novatel_time']
imu_diff['vert_accel'] = imu_diff[fields['vert_accel_nov']] / imu_diff['novatel_time']
imu_diff['lin_accel'] = np.sqrt(imu_diff['lat_accel'] ** 2 + imu_diff['long_accel'] ** 2 + imu_diff['vert_accel'] ** 2)

## setup figure
plt.figure(7)
plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['yaw'], label="derived")
plt.ylabel("Yaw rate (rad/s)")
finish_plot("Yaw rate: calculated from Novatel IMU", save_figs)

# lateral accel, novatel vs imu
plt.figure(8)
plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['lat_accel'], label = "novatel")
plt.scatter(dfs['imu'].elapsed_time, dfs['imu'][fields['lat_accel']], label = "imu")
plt.ylabel("Lateral acceleration (m/s^2)")
plt.ylim(-5,5)
plt.figtext(0.99, 0.01,
 '{} of {} novatel data outside plot range; min {:.2f}; max {:.2f}'.format(
     len(imu_diff.loc[abs(imu_diff['lat_accel']) > 5, 'lat_accel']),
     len(imu_diff['lat_accel']),
     np.nanmin(imu_diff['lat_accel']),
     np.nanmax(imu_diff['lat_accel'])
 ), horizontalalignment='right')
finish_plot("Lateral acceleration (novatel vs. imu)", save_figs)

# longitudinal accel, novatel vs imu
plt.figure(9)
plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['long_accel'], label = "novatel")
plt.scatter(dfs['imu'].elapsed_time, dfs['imu'][fields['long_accel']], label = "imu")
plt.ylabel("Longitudinal acceleration (m/s^2)")
plt.ylim(-5,5)
plt.figtext(0.99, 0.01,
 '{} of {} novatel data outside plot range; min {:.2f}; max {:.2f}'.format(
     len(imu_diff.loc[abs(imu_diff['long_accel']) > 5, 'long_accel']),
     len(imu_diff['long_accel']),
     np.nanmin(imu_diff['long_accel']),
     np.nanmax(imu_diff['long_accel'])
 ), horizontalalignment='right')
finish_plot("Longitudinal acceleration (novatel vs. imu)", save_figs)

# linear accel, commanded vs actual (novatel)
# vehicle_cmd has two different acceleration command values, but neither seem to make sense
plt.figure(10)
# plt.scatter(df_cmd.elapsed_time, df_cmd.accel, label = "commanded") # this is always all 0s
plt.scatter(dfs['cmd'].elapsed_time, dfs['cmd'][fields['accel_cmd']], label = "commanded")
plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['lin_accel'], label = "actual")
plt.ylabel("Acceleration (m/s^2)")
plt.ylim(-5,5)
plt.figtext(0.99, 0.01,
 '{} of {} commands outside plot range; min {:.2f}; max {:.2f}'.format(
     len(dfs['cmd'].loc[abs(dfs['cmd'][fields['accel_cmd']]) > 5, fields['accel_cmd']]),
     len(dfs['cmd'][fields['accel_cmd']]),
     min(dfs['cmd'][fields['accel_cmd']]),
     max(dfs['cmd'][fields['accel_cmd']])
 ), horizontalalignment='right')
finish_plot("Acceleration (commanded vs. actual)", save_figs)

fig = plt.figure(11)
ax1 = fig.add_subplot()

color11 = 'tab:red'
color12 = 'tab:orange'
ax1.set_ylabel('Steering angle (rad)', color=color11)
ax1.scatter(dfs['steer_cmd'].elapsed_time, dfs['steer_cmd'][fields['steer_cmd']], label = "steer commanded", color=color11)
ax1.scatter(dfs['steer'].elapsed_time, dfs['steer'][fields['steer_act']], label = "steer actual", color=color12)
ax1.tick_params(axis='y', labelcolor=color11)
ax1.legend()

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color21 = 'tab:blue'
color22 = 'tab:green'
ax2.set_ylabel('Acceleration (m/s^2)', color=color21)  # we already handled the x-label with ax1
ax2.scatter(dfs['cmd'].elapsed_time, dfs['cmd'][fields['accel_cmd']], label = "accel commanded", color=color21)
ax2.scatter(dfs['imu'].elapsed_time, dfs['imu'][fields['long_accel']], label = "accel actual", color=color22)
plt.ylim(-5,5) # reasonable acceleration limits
ax2.tick_params(axis='y', labelcolor=color21)

fig.tight_layout()  # otherwise the right y-label is slightly clipped
finish_plot("Steering and Acceleration (commanded vs. actual)", save_figs)
'''
plt.show()