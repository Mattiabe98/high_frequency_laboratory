import pandas as pd

essentialOnly = True


def import_csv():
    df = pd.DataFrame()
    k = 0
    morefiles = True
    filename = "csv to parse\Probe_toParse\Probe_1810_0_MS1.csv"
    while (morefiles):
        try:
            df_temp = pd.read_csv(filename)
            df_temp.insert(0, 'Point ID', '')
            df_temp['Point ID'] = k
            df = pd.concat([df, df_temp], ignore_index=True)
        except Exception as err:
            morefiles = False
            print(err)
        else:
            k += 1
            filename = "csv to parse\Probe_toParse\Probe_1810_" + str(k) + "_MS1.csv"
    return (df)


def filter_measurements(original_df):
    new_df = pd.DataFrame()
    first_run = True
    direction = 0  # 0: N, 1: E, 2: W, 3: O
    # Iterate over the original dataframe
    for index, row in original_df.iterrows():
        # Check the condition for each row
        if row['NR PCC DL PHY Throughput(Mbit/s)'] > 100:
            # Get the indices of the selected rows and the following 38 rows
            selected_indices = original_df.index[index:index + 37]

            # Check if any of the selected indices are already saved in the new dataframe
            if any(selected_indices.isin(new_df.index)):
                continue  # Skip this iteration if any selected indices are already saved
            # Append the selected rows and the following 38 rows to the new dataframe
            if first_run == True:
                new_df.insert(0, 'direction', '')
                first_run = False
            new_df = pd.concat([new_df, original_df.loc[selected_indices]])
            match direction:
                case 0:
                    new_df.loc[selected_indices, 'direction'] = "N"
                case 1:
                    new_df.loc[selected_indices, 'direction'] = "E"
                case 2:
                    new_df.loc[selected_indices, 'direction'] = "S"
                case 3:
                    new_df.loc[selected_indices, 'direction'] = "W"
            if direction == 3:
                direction = 0
            else:
                direction += 1
    return new_df


if __name__ == '__main__':
    df = import_csv()
    filtered_df = filter_measurements(df)
    if essentialOnly:
        useful_data = filtered_df[['direction', 'Latitude', 'Longitude', 'NR PCC UL PHY Throughput(Mbit/s)',
                                   'NR PCC DL PHY Throughput(Mbit/s)', 'NR PCC UL Avg MCS', 'NR PCC DL Avg MCS',
                                   'NR PCC SS Beam Ant0 RSRP 0(dBm)', 'NR PCC SS Beam Ant0 RSRP 1(dBm)',
                                   'NR PCC SS Beam Ant0 RSRP 2(dBm)', 'NR PCC SS Beam Ant0 RSRP 3(dBm)',
                                   'NR PCC SS Beam Ant0 RSRP 4(dBm)', 'NR PCC SS Beam Ant0 RSRP 5(dBm)',
                                   'NR PCC SS Beam Ant0 RSRP 6(dBm)', 'NR PCC SS Beam Ant0 RSRP 7(dBm)',
                                   'NR PCC SS Beam Idx0', 'NR PCC SS Beam Idx1', 'NR PCC SS Beam Idx2',
                                   'NR PCC SS Beam Idx3', 'NR PCC SS Beam Idx4', 'NR PCC SS Beam Idx5',
                                   'NR PCC SS Beam Idx6', 'NR PCC SS Beam Idx7', 'NR PCC SS Beam ID']].copy()
        # useful_data['id'] = range(0, len(useful_data))
        # first_column = useful_data.pop('id')
        useful_data.insert(0, 'id', range(0, len(useful_data)))
        useful_data.rename(
            columns={'Latitude': 'lat', 'Longitude': 'long', 'NR PCC UL PHY Throughput(Mbit/s)': 'throughput_up',
                     'NR PCC DL PHY Throughput(Mbit/s)': 'throughput_down', 'NR PCC UL Avg MCS': 'mcs_up',
                     'NR PCC DL Avg MCS': 'mcs_down', 'NR PCC SS Beam Ant0 RSRP 0(dBm)': 'rsrp0',
                     'NR PCC SS Beam Ant0 RSRP 1(dBm)': 'rsrp1', 'NR PCC SS Beam Ant0 RSRP 2(dBm)': 'rsrp2',
                     'NR PCC SS Beam Ant0 RSRP 3(dBm)': 'rsrp3', 'NR PCC SS Beam Ant0 RSRP 4(dBm)': 'rsrp4',
                     'NR PCC SS Beam Ant0 RSRP 5(dBm)': 'rsrp5', 'NR PCC SS Beam Ant0 RSRP 6(dBm)': 'rsrp6',
                     'NR PCC SS Beam Ant0 RSRP 7(dBm)': 'rsrp7', 'NR PCC SS Beam Idx0': 'beam_id0',
                     'NR PCC SS Beam Idx1': 'beam_id1', 'NR PCC SS Beam Idx2': 'beam_id2',
                     'NR PCC SS Beam Idx3': 'beam_id3', 'NR PCC SS Beam Idx4': 'beam_id4',
                     'NR PCC SS Beam Idx5': 'beam_id5', 'NR PCC SS Beam Idx6': 'beam_id6',
                     'NR PCC SS Beam Idx7': 'beam_id7', 'NR PCC SS Beam ID': 'selected_beam'}, inplace=True)
        useful_data.to_csv('filtered_essential.csv', index=False)
    else:
        filtered_df.to_csv('filtered_out.csv', index=False)
