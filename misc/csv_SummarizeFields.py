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
    data_folder = os.path.dirname(os.getcwd())
    # all_sensor_files = glob.glob(os.path.join(data_folder, '11-2020 CARMA Trial Run',
    #                                           'Data Files_All Sensors ON', '*.csv'))
    # carma_only_files = glob.glob(os.path.join(data_folder, '11-2020 CARMA Trial Run',
    #                                           'Data Files_CARMA Only', '*.csv'))
    jan_run_files = glob.glob(os.path.join(data_folder, '01-20-2021_Trial_Run', '*.csv'))

    # all_sensor_results = pd.DataFrame(columns=['Filename', 'Number of Rows', 'Min Timestamp',
    #                                            'Max Timestamp', 'Fields'])
    # carma_only_results = pd.DataFrame(columns=['Filename', 'Number of Rows', 'Min Timestamp',
    #                                            'Max Timestamp', 'Fields'])
    jan_run_results = pd.DataFrame(columns=['Filename', 'Number of Rows', 'Min Timestamp', 'Max Timestamp', 'Fields'])

    # for file in all_sensor_files:
    #     try:
    #         data_file = pd.read_csv(file)
    #         path_to, the_file_name = os.path.split(file)
    #         temp_row = {'Filename': the_file_name, 'Number of Rows': len(data_file.index)}
    #         if 'rosbagTimestamp' in data_file.columns:
    #             temp_row['Min Timestamp'] = data_file['rosbagTimestamp'].min()
    #             temp_row['Max Timestamp'] = data_file['rosbagTimestamp'].max()
    #         else:
    #             temp_row['Min Timestamp'] = np.nan
    #             temp_row['Max Timestamp'] = np.nan
    #         fields_list = data_file.columns.values.tolist()
    #         temp_row['Fields'] = ';'.join(fields_list)
    #         all_sensor_results = all_sensor_results.append(temp_row, ignore_index=True)
    #     except Exception as e:
    #         print('Error processing file {}.'.format(file))
    #         print(e)

    # for file in carma_only_files:
    #     try:
    #         data_file = pd.read_csv(file)
    #         path_to, the_file_name = os.path.split(file)
    #         temp_row = {'Filename': the_file_name, 'Number of Rows': len(data_file.index)}
    #         if 'rosbagTimestamp' in data_file.columns:
    #             temp_row['Min Timestamp'] = data_file['rosbagTimestamp'].min()
    #             temp_row['Max Timestamp'] = data_file['rosbagTimestamp'].max()
    #         else:
    #             temp_row['Min Timestamp'] = np.nan
    #             temp_row['Max Timestamp'] = np.nan
    #         fields_list = data_file.columns.values.tolist()
    #         temp_row['Fields'] = ';'.join(fields_list)
    #         carma_only_results = carma_only_results.append(temp_row, ignore_index=True)
    #     except Exception as e:
    #         print('Error processing file {}.'.format(file))
    #         print(e)

    for file in jan_run_files:
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
            jan_run_results = jan_run_results.append(temp_row, ignore_index=True)
        except Exception as e:
            print('Error processing file {}.'.format(file))
            print(e)

    # all_sensor_output = os.path.join(data_folder, '11-2020 CARMA Trial Run', 'all_sensor_data_files.csv')
    # carma_only_output = os.path.join(data_folder, '11-2020 CARMA Trial Run', 'carma_only_data_files.csv')
    jan_run_output = os.path.join(data_folder, '01-20-2021_Trial_Run', 'jan_run_data_files.csv')

    # with open(all_sensor_output, "w", newline='') as f:
    #     all_sensor_results.to_csv(f, index=False)

    # with open(carma_only_output, "w", newline='') as f:
    #     carma_only_results.to_csv(f, index=False)

    with open(jan_run_output, "w", newline='') as f:
        jan_run_results.to_csv(f, index=False)


if __name__ == "__main__":
    main()

