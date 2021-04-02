# -*- coding: utf-8 -*-
"""
Created on Mon Mar 22 15:56:35 2021

@author: ian.berg
"""
import rosbag
bag = rosbag.Bag("LS_SMPL_v3.5.1_r11_down-selected.bag")
topic_list = bag.get_type_and_topic_info() # like `rosbag info` in ROS

#convert to df
import json
import pandas as pd
topics = json.loads(json.dumps(topic_list))
df = pd.DataFrame.from_dict(topics[1]).transpose()
df.index.rename("topic_name", True)
df = df.rename(columns={0:"msg_spec_name", 1:"count"})
df.to_csv("downselected_lexus2.csv")

# get first object in external objects topic
for topic, msg, t in bag.read_messages(topics=["/environment/external_objects"]):
    if msg != []:
        for obj in msg.objects:
            print(obj)
            break
        break