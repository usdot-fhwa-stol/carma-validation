# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# setting up
import boto3
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString
import mpld3


# %%
# cleaning up loading the topics
def load_topic(csv_name, bucket = 'preprocessed-carma-core-validation'):
    s3_client = boto3.client('s3')
    file_name = "csvfiles/Core_Validation_Testing/Facility_Summit_Point/Vehicle_Silver_Lexus/20210415/LS_SPLMS_v3.5.3_r18_down-selected/" + csv_name
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

def finish_plot(plot_title, save_fig="off"):
        plt.xlabel("Time (elapsed seconds)")
        plt.legend(markerscale=3)
        plt.grid(True, alpha=0.5)
        plt.title(plot_title) # + "\n" + run)
        if save_fig == "png":
            plt.savefig("Figure_{}.png".format(plt.gcf().number))
        elif save_fig == "html":
            mpld3.save_html(plt.gcf(), "Figure_{}.html".format(plt.gcf().number))


# %%
dfs = {}
dfs["rd_objs"] = pd.read_csv("core_validation/environment_roadway_objects.csv")
dfs["sv_pose"] = load_topic("localization_current_pose.csv")
dfs["sv_lane"] = load_topic("guidance_route_state.csv")
dfs = calc_elapsed_time(dfs)


# %%
# trip to what we want to join, and set type to int64 for roadway objects
# then ensure sorted by rosbagTimestamp for merge_asof 
dfs["sv_pose"] = dfs["sv_pose"].sort_values("rosbagTimestamp")
dfs["sv_pose_t"] =  dfs["sv_pose"][["rosbagTimestamp","x","y","z"]]
dfs["sv_pose_t"] = dfs["sv_pose_t"].rename(columns={"x":"sv_x", "y":"sv_y", "z":"sv_z"})
dfs["sv_lane_t"] =  dfs["sv_lane"][["rosbagTimestamp","lanelet_id","cross_track", "lanelet_downtrack"]]
dfs["sv_lane_t"] = dfs["sv_lane_t"].rename(columns={"lanelet_id": "sv_lanelet", "cross_track": "sv_cross", "lanelet_downtrack": "sv_down"})

dfs["rd_objs"].rosbagTimestamp = dfs["rd_objs"].rosbagTimestamp.astype("int64")
dfs["rd_objs"] = dfs["rd_objs"].sort_values("rosbagTimestamp", ignore_index = True)
dfs["sv_pose_t"] = dfs["sv_pose_t"].sort_values("rosbagTimestamp", ignore_index = True)
dfs["sv_lane_t"] = dfs["sv_lane_t"].sort_values("rosbagTimestamp", ignore_index = True)


# %%
df = pd.merge_asof(dfs["rd_objs"], dfs["sv_pose_t"], on="rosbagTimestamp", direction='nearest')


# %%
df = pd.merge_asof(df, dfs["sv_lane_t"], on="rosbagTimestamp", direction='nearest')


# %%
df = df[df["sv_lanelet"] > 0] # filter out before the vehicle has localized itself


# %%
# first handle the easy case: POV is in the same lanelet as the SV
df_easy = df[df["lanelet_id"]==df["sv_lanelet"]]
df_easy = df_easy.assign(dt_diff = df_easy["down_track"] - df_easy["sv_down"])
df_easy = df_easy[df_easy["dt_diff"] > 0]
# based on https://stackoverflow.com/questions/15705630/get-the-rows-which-have-the-max-value-in-groups-using-groupby
idx = df_easy.groupby("rosbagTimestamp")["dt_diff"].transform("min") == df_easy['dt_diff']
easy_results = df_easy[idx]


# %%
# filter out the remaining work to do
df_remaining = df[~df["rosbagTimestamp"].isin(easy_results["rosbagTimestamp"])]


# %%
sp_loop_right_lane_ids = [23813,24078,24564,24972,25521,25585,25731,27738,27817,28737,29729]
sp_loop_left_lane_ids = [23812,24077,24563,24971,25520,25584,25730,27737,27816,28736,29728]
df_remaining[df_remaining["sv_lanelet"].isin(sp_loop_right_lane_ids)] # returns them all, so we won't worry about the left lane

df_remaining = df_remaining.assign(sv_lanelet_ahead = df_remaining["sv_lanelet"].apply(lambda x: sp_loop_right_lane_ids[(sp_loop_right_lane_ids.index(x)+1) % len(sp_loop_right_lane_ids)]))


# %%
df_remaining[df_remaining["lanelet_id"]==df_remaining["sv_lanelet_ahead"]]
#again empty, so not dealing with for now


# %%
plt.rcParams['scatter.marker'] = '.'
plt.rcParams['figure.figsize'] = [8, 6]
plt.rcParams['lines.markersize'] = 3
plt.figure(3)
plt.scatter(df_easy.elapsed_time, df_easy.dt_diff)
finish_plot("Distance to nearest object ahead in same lanelet (centroid to centroid)") #, "png")


# %%
plt.show()


