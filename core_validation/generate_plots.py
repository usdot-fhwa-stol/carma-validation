# setting up
import boto3
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString
import mpld3

# helper from misc folder
def csv_loc_from_run(run_name):
    # TODO: generalize or pass as input
    csv_loc = "csvfiles/Core_Validation_Testing/Facility_Summit_Point/"
    
    veh = run_name.split("_")[0]
    run_no = run_name.split("_")[-1]
    run_date = "20210318"

    if veh == "P":
        csv_loc = csv_loc + "Vehicle_Black_Pacifica/"
        if int(run_no[1:]) >= 15:
            run_date = "20210413"
    elif veh == "LS":
        csv_loc = csv_loc + "Vehicle_Silver_Lexus/"
        if int(run_no[1:]) >= 12:
            run_date = "20210415"
    elif veh == "F":
        csv_loc = csv_loc + "Vehicle_White_Ford/"
        if int(run_no[1:]) >= 13:
            run_date = "20210415"
    if run_date == "20210318":
        csv_loc = csv_loc + "{}/{}_down-selected/".format(run_date, run_no)
    else:
        csv_loc = csv_loc + "{}/{}_down-selected/".format(run_date, run_name)
    return csv_loc


# cleaning up loading the topics
def load_topic(bucket, run, csv_name):
    s3_client = boto3.client('s3')
    file_name = csv_loc_from_run(run) + csv_name
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


def generate_plots_for_run(run = "LS_SMPL_v3.5.1_r11", plots = [1,2,3,4,5,6], plot_type = "scatter", save_figs = "off"):
# run is the name of the run
# plots are which of 1-6 should be generated (0 is always generated for reference)
# type is either "scatter" or "line"
# save figs options are "png", "html"; anything else is equiv to don't save


    def finish_plot(plot_title, save_fig, trim_plot=True):
        plt.xlabel("Time (elapsed seconds)")
        # TODO: should not reference outside variables without passing them in
        # I think nesting this in a "generate plots" fn resolves this?
        if trim_plot:
            plt.xlim(carma_start_time-10,carma_end_time+10)
        left, right = plt.xlim()
        bottom, top = plt.ylim()
        if save_fig == "html":
            plt.fill_betweenx([bottom, top], left, carma_start_time, color='lightblue', alpha=0.5)
            plt.fill_betweenx([bottom, top], carma_end_time, right, color='lightblue', alpha=0.5)
            plt.ylim(bottom, top)
        else:
            plt.axvspan(left, carma_start_time, color='lightblue', alpha=0.5)
            plt.axvspan(carma_end_time, right, color='lightblue', alpha=0.5)
        plt.legend(markerscale=3)
        plt.grid(True, alpha=0.5)
        plt.title(plot_title + "\n" + run)
        if save_fig == "png":
            plt.savefig("C:/Users/Public/Documents/outplots/{}/{}/Figure_{}.png".format(run, plot_type, plt.gcf().number))
        elif save_fig == "html":
            mpld3.save_html(plt.gcf(), "C:/Users/Public/Documents/outhtml/{}/{}/Figure_{}.html".format(run, plot_type, plt.gcf().number))



    bucket = 'preprocessed-carma-core-validation'
    #run = "LS_SMPL_v3.5.1_r11"
    #run = "F_SPLMS_v3.5.1_r11"
    #run = "P_SPLMS_v3.5.1_r14"
    veh = run.split("_")[0]
    if save_figs == "png":
        if not os.path.exists("C:/Users/Public/Documents/outplots/{}/{}".format(run, plot_type)):
            os.makedirs("C:/Users/Public/Documents/outplots/{}/{}".format(run, plot_type))
    elif save_figs == "html":
        if not os.path.exists("C:/Users/Public/Documents/outhtml/{}/{}".format(run, plot_type)):
            os.makedirs("C:/Users/Public/Documents/outhtml/{}/{}".format(run, plot_type))

    # load necessary topics
    topics = {}
    topics['state'] = "guidance_state.csv"
    topics['cmd'] = "hardware_interface_arbitrated_speed_commands.csv"
    topics['corrimudata'] = "hardware_interface_corrimudata.csv"
    topics['pose'] = "localization_current_pose.csv"
    topics['vel_accel'] = "hardware_interface_velocity_accel_cov.csv"

    fields = {}
    fields['state'] = 'state'
    fields['spd_cmd'] = 'speed'
    fields['accel_lim'] = 'acceleration_limit'
    fields['decel_lim'] = 'deceleration_limit'
    fields['yaw_rate_nov'] = 'yaw_rate'
    fields['lat_accel_nov'] = 'lateral_acceleration'
    fields['long_accel_nov'] = 'longitudinal_acceleration'
    fields['vert_accel_nov'] = 'vertical_acceleration'
    fields['pose_x'] = 'x'
    fields['pose_y'] = 'y'
    fields['accel'] = 'accleration' #yes this is a typo but it's how it's spelled in the msg spec

    if veh == "P":
        topics['spd'] = "hardware_interface_misc_report.csv"
        #topics['imu'] = "hardware_interface_imu_data_raw.csv"
        topics['steer'] = "hardware_interface_steering_report.csv"
        topics['steer_cmd'] = "hardware_interface_steering_cmd.csv"
        topics['throttle'] = "hardware_interface_accelerator_pedal_report.csv"
        topics['throttle_cmd'] = "hardware_interface_accelerator_pedal_cmd.csv"
        topics['brake'] = "hardware_interface_brake_report.csv"
        topics['brake_cmd'] = "hardware_interface_brake_cmd.csv"

        fields['spd'] = 'vehicle_speed'
        #fields['long_accel'] = 'x.2'
        #fields['lat_accel'] = 'y.2'
        #fields['vert_accel'] = 'z.2'
        fields['steer_cmd'] = 'angle_cmd'
        fields['steer_act'] = 'steering_wheel_angle'
        fields['throttle_cmd'] = 'pedal_cmd'
        fields['throttle_act'] = 'pedal_output'
        fields['brake_cmd'] = 'pedal_cmd'
        fields['brake_act'] = 'pedal_output'
    elif veh == "LS":
        topics['spd'] = "hardware_interface_pacmod_parsed_tx_vehicle_speed_rpt.csv"
        #topics['imu'] = "hardware_interface_imu_raw.csv"
        topics['steer'] = "hardware_interface_pacmod_parsed_tx_steer_rpt.csv"
        topics['steer_cmd'] = "hardware_interface_pacmod_as_rx_steer_cmd.csv"
        topics['throttle'] = "hardware_interface_pacmod_parsed_tx_accel_rpt.csv"
        topics['throttle_cmd'] = "hardware_interface_pacmod_as_rx_accel_cmd.csv"
        topics['brake'] = "hardware_interface_pacmod_parsed_tx_brake_rpt.csv"
        topics['brake_cmd'] = "hardware_interface_pacmod_as_rx_brake_cmd.csv"
        topics['yaw_rate'] = "hardware_interface_pacmod_parsed_tx_yaw_rate_rpt.csv"

        fields['spd'] = 'vehicle_speed'
        #fields['long_accel'] = 'x.2'
        #fields['lat_accel'] = 'y.2'
        #fields['vert_accel'] = 'z.2'
        fields['steer_cmd'] = 'command'
        fields['steer_act'] = 'output'
        fields['throttle_cmd'] = 'command'
        fields['throttle_act'] = 'output'
        fields['brake_cmd'] = 'command'
        fields['brake_act'] = 'output'
        fields['yaw_rate_act'] = 'yaw_rate'
    elif veh == "F":
        topics['spd'] = "hardware_interface_ds_fusion_steering_report.csv"
        #topics['imu'] = "hardware_interface_ds_fusion_imu_data_raw.csv"
        topics['steer'] = "hardware_interface_ds_fusion_steering_report.csv"
        topics['steer_cmd'] = "hardware_interface_ds_fusion_steering_cmd.csv"
        topics['throttle'] = "hardware_interface_ds_fusion_throttle_report.csv"
        topics['throttle_cmd'] = "hardware_interface_ds_fusion_throttle_cmd.csv"
        topics['brake'] = "hardware_interface_ds_fusion_brake_report.csv"
        topics['brake_cmd'] = "hardware_interface_ds_fusion_brake_cmd.csv"

        fields['spd'] = 'speed'
        #fields['long_accel'] = 'x.2'
        #fields['lat_accel'] = 'y.2'
        #fields['vert_accel'] = 'z.2'
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
    if save_figs == "html":
        plt.rcParams['lines.markersize'] = 1
    else:
        plt.rcParams['lines.markersize'] = 3
    plt.rcParams['figure.figsize'] = [8, 6]

    # find longest stretch of CARMA state = 4 during run
    z, p, ia = rle(dfs['state'].state == 4)
    carma_never_engaged = False
    try:
        carma_start_ind = p[z == max(z[ia])][0]
        carma_end_ind = carma_start_ind + z[z == max(z[ia])][0] - 1
        carma_start_time = dfs['state'].loc[carma_start_ind, 'elapsed_time']
        carma_end_time = dfs['state'].loc[carma_end_ind, 'elapsed_time']
    except ValueError:
        carma_start_time = min(dfs['state'].elapsed_time)
        carma_end_time = max(dfs['state'].elapsed_time)
        carma_never_engaged = True

    if carma_never_engaged:
        plt.rcParams['axes.facecolor'] = 'lightblue'

    # get state of CARMA system (4=ENGAGED) 
        # get state of CARMA system (4=ENGAGED) 
    # get state of CARMA system (4=ENGAGED) 
    #always generate for reference
    plt.figure(0)
    if plot_type == "scatter":
        plt.scatter(dfs['state'].elapsed_time, dfs['state'][fields['state']], label="state")
    elif plot_type == "line":
        plt.plot(dfs['state'].elapsed_time, dfs['state'][fields['state']], label="state")
    finish_plot("CARMA System state", False)

    # speed, commanded vs actual
    if 1 in plots:
        plt.figure(1)
        if plot_type == "scatter":
            plt.scatter(dfs['cmd'].elapsed_time, dfs['cmd'][fields['spd_cmd']], label = "commanded")
            plt.scatter(dfs['spd'].elapsed_time, dfs['spd'][fields['spd']], label = "actual")
        elif plot_type == "line":
            plt.plot(dfs['cmd'].elapsed_time, dfs['cmd'][fields['spd_cmd']], label = "{}/{}".format(topics['cmd'], fields['spd_cmd']))
            plt.plot(dfs['spd'].elapsed_time, dfs['spd'][fields['spd']], label = "{}/{}".format(topics['spd'], fields['spd']))
        plt.ylabel("Speed (m/s)")
        finish_plot("Speed (commanded vs. actual)", save_figs)

    # linear accel, commanded limits vs actual
    if 2 in plots:
        plt.figure(2)
        if plot_type == "scatter":
            plt.scatter(dfs['cmd'].elapsed_time, dfs['cmd'][fields['accel_lim']], label = "accel limit")
            plt.scatter(dfs['cmd'].elapsed_time, -1 * dfs['cmd'][fields['decel_lim']], label = "decel limit")
            plt.scatter(dfs['vel_accel'].elapsed_time, dfs['vel_accel'][fields['accel']], label = "actual")
        elif plot_type == "line":
            plt.plot(dfs['cmd'].elapsed_time, dfs['cmd'][fields['accel_lim']], label = "{}/{}".format(topics['cmd'], fields['accel_lim']))
            plt.plot(dfs['cmd'].elapsed_time, -1 * dfs['cmd'][fields['decel_lim']], label = "{}/{}".format(topics['cmd'], fields['decel_lim']))
            plt.plot(dfs['vel_accel'].elapsed_time, dfs['vel_accel'][fields['accel']], label = "{}/{}".format(topics['vel_accel'], fields['accel']))
        plt.ylabel("Acceleration (m/s^2)")
        finish_plot("Linear acceleration (commanded limits vs. actual)", save_figs)

    # crosstrack distance from vehicle centroid to center dashed line 
        # crosstrack distance from vehicle centroid to center dashed line 
    # crosstrack distance from vehicle centroid to center dashed line 
    if 3 in plots:
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
        if plot_type == "scatter":
            plt.scatter(gdf_pose.elapsed_time, gdf_pose.dist_to_cl, label="distance") 
        elif plot_type == "line":
            plt.plot(gdf_pose.elapsed_time, gdf_pose.dist_to_cl, label="distance") 
        plt.ylabel("Crosstrack distance to road centerline (m)")
        plt.ylim(0,3.4) # Tim's assumption: lane width is 3.4m = 11ft
        finish_plot("Distance: vehicle centroid to road centerline", save_figs)

    # throttle pct actual vs commanded
    if 4 in plots:
        plt.figure(4)
        if plot_type == "scatter":
            plt.scatter(dfs['throttle_cmd'].elapsed_time, dfs['throttle_cmd'][fields['throttle_cmd']], label="commanded")
            plt.scatter(dfs['throttle'].elapsed_time, dfs['throttle'][fields['throttle_act']], label="actual")
        elif plot_type == "line":
            plt.plot(dfs['throttle_cmd'].elapsed_time, dfs['throttle_cmd'][fields['throttle_cmd']], label="{}/{}".format(topics['throttle_cmd'], fields['throttle_cmd']))
            plt.plot(dfs['throttle'].elapsed_time, dfs['throttle'][fields['throttle_act']], label="{}/{}".format(topics['throttle'], fields['throttle_act']))
        if veh == "F":
            plt.ylabel("Throttle (range 0.15 to 0.80)")
        else:
            plt.ylabel("Throttle (percent))")
        finish_plot("Throttle (commanded vs. actual)", save_figs)

    # steering angle actual vs commanded
    if 5 in plots:
        plt.figure(5)
        if plot_type == "scatter":
            plt.scatter(dfs['steer_cmd'].elapsed_time, dfs['steer_cmd'][fields['steer_cmd']], label="commanded")
            plt.scatter(dfs['steer'].elapsed_time, dfs['steer'][fields['steer_act']], label="actual")
        elif plot_type == "line":
            plt.plot(dfs['steer_cmd'].elapsed_time, dfs['steer_cmd'][fields['steer_cmd']], label="{}/{}".format(topics['steer_cmd'], fields['steer_cmd']))
            plt.plot(dfs['steer'].elapsed_time, dfs['steer'][fields['steer_act']], label="{}/{}".format(topics['steer'], fields['steer_act']))
        plt.ylabel("Steering angle (rad)")
        finish_plot("Steering (commanded vs. actual)", save_figs)

    # brake pct actual vs commanded
    if 6 in plots:
        plt.figure(6)
        if plot_type == "scatter":
            plt.scatter(dfs['brake_cmd'].elapsed_time, dfs['brake_cmd'][fields['brake_cmd']], label="commanded")
            plt.scatter(dfs['brake'].elapsed_time, dfs['brake'][fields['brake_act']], label="actual")
        elif plot_type == "line":
            plt.plot(dfs['brake_cmd'].elapsed_time, dfs['brake_cmd'][fields['brake_cmd']], label="{}/{}".format(topics['brake_cmd'], fields['brake_cmd']))
            plt.plot(dfs['brake'].elapsed_time, dfs['brake'][fields['brake_act']], label="{}/{}".format(topics['brake'], fields['brake_act']))
        if veh == "F":
            plt.ylabel("Braking (range 0.15 to 0.80)")
        else:
            plt.ylabel("Braking (percent)")
        finish_plot("Braking (commanded vs. actual)", save_figs)

#generate_plots_for_run("P_SPLMS_v3.5.3_r28")
#plt.show()

all_runs = [
"P_SPLMS_v3.5.3_r28"
]

for runid in all_runs:
    # generate all, both types
    generate_plots_for_run(run=runid, save_figs="html")
    plt.close("all")
    generate_plots_for_run(run=runid, plot_type="line", save_figs="html")
    plt.close("all")
    print(runid)

'''
dfs['corrimudata']['novatel_time'] = dfs['corrimudata'].secs + dfs['corrimudata'].nsecs/1000000000.0
# calculate yaw rate, lateral acceleration, longitundinal acceleration, vertical acceleration from Novatel IMU
imu_diff = dfs['corrimudata']['novatel_time'].diff().to_frame()
imu_diff['yaw_rate'] = dfs['corrimudata'][fields['yaw_rate_nov']] / imu_diff['novatel_time']
imu_diff['lat_accel'] = dfs['corrimudata'][fields['lat_accel_nov']] / imu_diff['novatel_time']
imu_diff['long_accel'] = dfs['corrimudata'][fields['long_accel_nov']] / imu_diff['novatel_time']
imu_diff['vert_accel'] = dfs['corrimudata'][fields['vert_accel_nov']] / imu_diff['novatel_time']

## setup figure
# Ford, Pacifica - yaw rate
if veh != "SL":
    plt.figure(7)
    plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['yaw_rate'], label="derived")
    plt.ylabel("Yaw rate (rad/s)")
    finish_plot("Yaw rate: calculated from Novatel IMU", save_figs)
else:
    # Lexus - yaw rate, novatel vs pacmod
    plt.figure(7)
    plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['yaw_rate'], label="novatel")
    plt.scatter(dfs['yaw_rate'].elapsed_time, dfs['yaw_rate'][fields['yaw_rate_act']], label = "pacmod")
    plt.ylabel("Yaw rate (rad/s)")
    finish_plot("Yaw rate (novatel vs. imu)", save_figs)

# lateral accel, novatel vs imu
plt.figure(8)
plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['lat_accel'], label = "novatel")
plt.scatter(dfs['imu'].elapsed_time, dfs['imu'][fields['lat_accel']], label = "imu")
plt.ylabel("Lateral acceleration (m/s^2)")
# plt.ylim(-5,5)
# plt.figtext(0.99, 0.01,
#  '{} of {} novatel data outside plot range; min {:.2f}; max {:.2f}'.format(
#      len(imu_diff.loc[abs(imu_diff['lat_accel']) > 5, 'lat_accel']),
#      len(imu_diff['lat_accel']),
#      np.nanmin(imu_diff['lat_accel']),
#      np.nanmax(imu_diff['lat_accel'])
#  ), horizontalalignment='right')
finish_plot("Lateral acceleration (novatel vs. imu)", save_figs)

# longitudinal accel, novatel vs imu
plt.figure(9)
plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['long_accel'], label = "novatel")
plt.scatter(dfs['imu'].elapsed_time, dfs['imu'][fields['long_accel']], label = "imu")
plt.ylabel("Longitudinal acceleration (m/s^2)")
# plt.ylim(-5,5)
# plt.figtext(0.99, 0.01,
#  '{} of {} novatel data outside plot range; min {:.2f}; max {:.2f}'.format(
#      len(imu_diff.loc[abs(imu_diff['long_accel']) > 5, 'long_accel']),
#      len(imu_diff['long_accel']),
#      np.nanmin(imu_diff['long_accel']),
#      np.nanmax(imu_diff['long_accel'])
#  ), horizontalalignment='right')
finish_plot("Longitudinal acceleration (novatel vs. imu)", save_figs)

# vertical accel, novatel vs imu
plt.figure(10)
plt.scatter(dfs['corrimudata'].elapsed_time, imu_diff['vert_accel'], label = "novatel")
plt.scatter(dfs['imu'].elapsed_time, dfs['imu'][fields['vert_accel']], label = "imu")
plt.ylabel("Vertical acceleration (m/s^2)")
# plt.ylim(-5,5)
# plt.figtext(0.99, 0.01,
#  '{} of {} novatel data outside plot range; min {:.2f}; max {:.2f}'.format(
#      len(imu_diff.loc[abs(imu_diff['vert_accel']) > 5, 'vert_accel']),
#      len(imu_diff['vert_accel']),
#      np.nanmin(imu_diff['vert_accel']),
#      np.nanmax(imu_diff['vert_accel'])
#  ), horizontalalignment='right')
finish_plot("Vertical acceleration (novatel vs. imu)", save_figs)


fig = plt.figure(11)
ax1 = fig.add_subplot()
ax1.set_xlabel('Time (elapsed seconds)')
plt.xlim(max(0,carma_start_time-10),carma_end_time+10)
left, right = plt.xlim()
bottom, top = plt.ylim()
plt.axvspan(left, carma_start_time, color='lightblue', alpha=0.5)
plt.axvspan(carma_end_time, right, color='lightblue', alpha=0.5)

color11 = 'tab:red'
color12 = 'tab:orange'
ax1.set_ylabel('Steering angle (rad)', color=color11)
ax1.scatter(dfs['steer_cmd'].elapsed_time, dfs['steer_cmd'][fields['steer_cmd']], label = "steer commanded", color=color11)
ax1.scatter(dfs['steer'].elapsed_time, dfs['steer'][fields['steer_act']], label = "steer actual", color=color12)
ax1.tick_params(axis='y', labelcolor=color11)
# ax1.legend(markerscale=3, loc='best')

ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

color21 = 'tab:blue'
color22 = 'tab:green'
ax2.set_ylabel('Lateral acceleration (m/s^2)', color=color21)  # we already handled the x-label with ax1
ax2.scatter(dfs['imu'].elapsed_time, dfs['imu'][fields['lat_accel']], label = "lat accel actual", color=color21)
# plt.ylim(-5,5) # reasonable acceleration limits
ax2.tick_params(axis='y', labelcolor=color21)

handles, labels = [(a+b) for a, b in zip(ax1.get_legend_handles_labels(), ax2.get_legend_handles_labels())]
plt.legend(handles, labels, markerscale=3)
plt.grid(True, alpha=0.5)
plt.title("Steering and Lateral acceleration (commanded vs. actual)" + "\n" + run)
plt.tight_layout()  # otherwise the right y-label is slightly clipped
# finish_plot("Steering and Lateral acceleration (commanded vs. actual)", save_figs)
'''
