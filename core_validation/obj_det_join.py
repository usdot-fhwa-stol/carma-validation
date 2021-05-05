# To add a new cell, type '# %%'
# To add a new markdown cell, type '# %% [markdown]'
# %%
# setting up
import boto3
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import geopandas as gpd
from shapely.geometry import Point, LineString
import mpld3
import random

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

# this still needs some work (e.g., on run 18 the outputs don't match guidance/route_state)
# but it's a start
def calc_lanelet_pos(pose_df):
    gdf = gpd.GeoDataFrame(pose_df, geometry=gpd.points_from_xy(pose_df.x, pose_df.y))
    
    lanelets = pd.read_csv("misc/sp_lanelets_with_wkt.csv")
    lanelets["not_centerline"] = np.where(lanelets["in_out"] == 'inner_lane',  lanelets['inner_wkt'], lanelets['outer_wkt'])
    lanelets = gpd.GeoDataFrame(lanelets, geometry= gpd.GeoSeries.from_wkt(lanelets["not_centerline"]))
    # find index of nearest non-centerline lane marking ... uniquely IDs the lane you're in
    # wouldn't work if the road was >2 lanes - KZ: could we sum distance to left lane marking and distance to right lane marking then find argmin?
    gdf["matching_lanelet_index"] = gdf.geometry.apply(lambda x: lanelets.distance(x).argmin())

    # change geometry to left-hand (outer, clockwise) lane marking 
    # since crosstrack distance is defined from it
    lanelets = lanelets.set_geometry(gpd.GeoSeries.from_wkt(lanelets.outer_wkt))
    lanelets_s = lanelets[["lanelet","geometry"]]
    gdf = gdf.merge(lanelets_s, how="left", left_on="matching_lanelet_index", right_index = True)

    # now match fields in guidance/route_state
    gdf = gdf.rename(columns={'lanelet': 'lanelet_id'})
    gdf["cross_track"] =gpd.GeoSeries(gdf["geometry_x"]).distance(gpd.GeoSeries(gdf["geometry_y"]))
    gdf["lanelet_downtrack"] =gpd.GeoSeries(gdf["geometry_y"]).project(gpd.GeoSeries(gdf["geometry_x"]))

    return gdf

# %%
dfs = {}
dfs["rd_objs"] = pd.read_csv('C:/Users/Public/Documents/outcsv/LS_r18_environment_roadway_objects.csv')
dfs["sv_pose"] = load_topic("localization_current_pose.csv")
try:
    dfs["sv_lane"] = load_topic("guidance_route_state.csv")
except:
    dfs["sv_lane"] = calc_lanelet_pos(dfs["sv_pose"])
dfs = calc_elapsed_time(dfs)


# %%
# trim to what we want to join, and set type to int64 for roadway objects
# then ensure sorted by rosbagTimestamp for merge_asof 
dfs["sv_pose"] = dfs["sv_pose"].sort_values("rosbagTimestamp")
dfs["sv_pose_t"] =  dfs["sv_pose"][["rosbagTimestamp","x","y","z"]]
dfs["sv_pose_t"] = dfs["sv_pose_t"].rename(columns={"x": "sv_x", "y": "sv_y", "z": "sv_z", "rosbagTimestamp": "rosbagTimestamp_p"})
dfs["sv_lane_t"] =  dfs["sv_lane"][["rosbagTimestamp","lanelet_id","cross_track", "lanelet_downtrack"]]
dfs["sv_lane_t"] = dfs["sv_lane_t"].rename(columns={"lanelet_id": "sv_lanelet", "cross_track": "sv_cross", "lanelet_downtrack": "sv_down", "rosbagTimestamp": "rosbagTimestamp_l"})

dfs["rd_objs"].rosbagTimestamp = dfs["rd_objs"].rosbagTimestamp.astype("int64")
dfs["rd_objs"] = dfs["rd_objs"].sort_values("rosbagTimestamp", ignore_index = True)
dfs["sv_pose_t"] = dfs["sv_pose_t"].sort_values("rosbagTimestamp_p", ignore_index = True)
dfs["sv_lane_t"] = dfs["sv_lane_t"].sort_values("rosbagTimestamp_l", ignore_index = True)


# %%
df = pd.merge_asof(dfs["rd_objs"], dfs["sv_pose_t"], left_on="rosbagTimestamp", right_on="rosbagTimestamp_p", direction='nearest')


# %%
df = pd.merge_asof(df, dfs["sv_lane_t"], left_on="rosbagTimestamp", right_on="rosbagTimestamp_l", direction='nearest')


# %%
df = df[df["sv_lanelet"] > 0] # filter out before the vehicle has localized itself


# %%
# first handle the easy case: POV is in the same lanelet as the SV
df_easy = df[df["lanelet_id"]==df["sv_lanelet"]]
df_easy = df_easy.assign(dt_diff = df_easy["down_track"] - df_easy["sv_down"])
df_easy = df_easy[df_easy["dt_diff"] > 0]
# based on https://stackoverflow.com/questions/15705630/get-the-rows-which-have-the-max-value-in-groups-using-groupby
idx = df_easy.groupby("rosbagTimestamp")["dt_diff"].transform("min") == df_easy['dt_diff']  # TODO: KZ - is it possible (seems pretty much impossible) for 2 mins to be equal to each other
easy_results = df_easy[idx]


# %%
# filter out the remaining work to do
df_remaining = df[~df["rosbagTimestamp"].isin(easy_results["rosbagTimestamp"])]


# %%
sp_loop_right_lane_ids = [23813,24078,24564,24972,25521,25585,25731,27738,27817,28737,29729]
sp_loop_left_lane_ids = [23812,24077,24563,24971,25520,25584,25730,27737,27816,28736,29728]
df_remaining_r = df_remaining[df_remaining["sv_lanelet"].isin(sp_loop_right_lane_ids)] # returns them all, so we won't worry about the left lane

df_remaining_r = df_remaining_r.assign(sv_lanelet_ahead = df_remaining_r["sv_lanelet"].apply(lambda x: sp_loop_right_lane_ids[(sp_loop_right_lane_ids.index(x)+1) % len(sp_loop_right_lane_ids)]))


# %%
df_remaining_r[df_remaining_r["lanelet_id"]==df_remaining_r["sv_lanelet_ahead"]]
#TODO: handle this case as well as left lane case


# %%
plt.rcParams['scatter.marker'] = '.'
plt.rcParams['figure.figsize'] = [8, 6]
plt.rcParams['lines.markersize'] = 3

# assign random color by object id
cs = {k: (random.random(), random.random(), random.random()) for k in df_easy["object_id"].drop_duplicates()}
cmap = ListedColormap(cs.values())

plt.figure(3)
plt.scatter(easy_results.elapsed_time, easy_results.dt_diff, c=easy_results.object_id, cmap=cmap)
plt.ylabel("Difference in downtrack distance (m)")
finish_plot("Downtrack distance to nearest object ahead in same lanelet (centroid to centroid)")

plt.show()

# %%
'''
import math
easy_results = easy_results.reset_index(drop=True)
easy_results["dist_act"]= (
    (easy_results["pos_x"]-easy_results["sv_x"])**2 +
    (easy_results["pos_y"]-easy_results['sv_y'])**2 +
    (easy_results['pos_z']-easy_results['sv_z'])**2)**0.5

easy_results["dif_dists"] = easy_results["dist_act"] - easy_results["dt_diff"]
# %%
plt.figure(4)
plt.scatter(easy_results.elapsed_time, easy_results.dif_dists)

plt.show()
# %%
'''
