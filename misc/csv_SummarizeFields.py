#!/usr/bin/env python
# coding: utf-8


# ---------------------------------------------------------------------------------------------------
# Name: cav_ReadData
#
# Summarizes data files from "11-2020 CARMA Trial Run" and "01-20-2021_Trial_Run" data dumps.
#
# ---------------------------------------------------------------------------------------------------
import os
import glob
import pandas as pd
import numpy as np
import pdb


def main():
    data_folder = 'C:/Users/kevin.zhang/Documents/Project_HW33A/CARMA Analytics/Preprocessed Data'
    run = 'WhiteFusion_Summit_Point_r11'
    run_files = glob.glob(os.path.join(data_folder, run, '*.csv'))

    run_results = pd.DataFrame(columns=['Filename', 'Number of Rows', 'Min Timestamp', 'Max Timestamp', 'Fields'])

    for file in run_files:
        try:
            data_file = pd.read_csv(file)
            path_to, the_file_name = os.path.split(file)
            temp_row = {'Filename': the_file_name, 'Number of Rows': len(data_file.index)}
            if 'rosbagTimestamp' in data_file.columns:
                temp_row['Min Timestamp'] = data_file['rosbagTimestamp'].min()
                temp_row['Max Timestamp'] = data_file['rosbagTimestamp'].max()
            else:
                temp_row['Min Timestamp'] = np.nan
                temp_row['Max Timestamp'] = np.nan
            fields_list = data_file.columns.values.tolist()
            temp_row['Fields'] = ';'.join(fields_list)
            run_results = run_results.append(temp_row, ignore_index=True)
        except Exception as e:
            print('Error processing file {}.'.format(file))
            print(e)

    run_output = os.path.join(data_folder, run + '_data_files.csv')

    with open(run_output, "w", newline='') as f:
        run_results.to_csv(f, index=False)


if __name__ == "__main__":
    main()

