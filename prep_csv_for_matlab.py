import pandas as pd

just_get_highest_rsrp = False

def split_dataframe(df, chunk_size=37):
    chunks = list()
    num_chunks = len(df) // chunk_size
    for i in range(num_chunks):
        chunks.append(df[i * chunk_size:(i + 1) * chunk_size])
    return chunks


def nemo_split(df_original):
    df_original['group'] = df_original['direction'].ne(df_original['direction'].shift()).cumsum()
    df_original = df_original.groupby('group')
    dfs = []
    for name, data in df_original:
        dfs.append(data)
    return dfs


if __name__ == '__main__':
    filename = "filtered_out.csv"
    df_original = pd.read_csv(filename)
    n = 0
    columns = ['id', 'direction', 'lat', 'long', 'avg_throughput_up', 'variance_throughput_up', 'avg_throughput_down',
               'variance_throughput_down', 'avg_highest_rsrp', 'variance_highest_rsrp', 'avg_mcs_up', 'variance_mcs_up',
               'avg_mcs_down', 'variance_mcs_down',
               'most_freq_beam']

    if just_get_highest_rsrp:
        df_original['highest_rsrp'] = df_original[
            ['rsrp0', 'rsrp1', 'rsrp2', 'rsrp3', 'rsrp4', 'rsrp5', 'rsrp6', 'rsrp7']].max(axis=1)
    else:
        rsrp_id = df_original.loc[:, 'beam_id0':'beam_id7'].isin(df_original['selected_beam']).idxmax(1)
        rsrp_id = rsrp_id.str.replace('beam_id', 'rsrp')
        for index, row in df_original.iterrows():
            df_original.at[index, 'highest_rsrp'] = df_original[rsrp_id[index]][index]
    # dfs = split_dataframe(df_original) #could've spliced every 37 rows but Nemo is not periodic..
    dfs = nemo_split(df_original)

    new_rows_list = []
    for dataframe in dfs:
        # DOWNLOAD
        download_mean = dataframe.loc[
            (dataframe["throughput_down"] - dataframe["throughput_up"] > 0), 'throughput_down'].mean()
        download_variance = dataframe.loc[
            (dataframe["throughput_down"] - dataframe["throughput_up"] > 0), 'throughput_down'].var()
        avg_mcs_down = dataframe.loc[(dataframe["throughput_down"] - dataframe["throughput_up"] > 0), 'mcs_down'].mean()
        variance_mcs_down = dataframe.loc[
            (dataframe["throughput_down"] - dataframe["throughput_up"] > 0), 'mcs_down'].var()
        # UPLOAD
        
        filter_thg_up = dataframe[dataframe['throughput_up'] > 0.05]
        if (len(filter_thg_up) > 0):
            dataframe = filter_thg_up  # remove samples saved when dl speedtest ended but ul
            # else not to filter is just trhougput
            
        # speedtest hasn't started yet
        upload_mean = dataframe.loc[
            (dataframe["throughput_up"] - dataframe["throughput_down"] > 0), 'throughput_up'].mean()
        upload_variance = dataframe.loc[
            (dataframe["throughput_up"] - dataframe["throughput_down"] > 0), 'throughput_up'].var()
        avg_mcs_up = dataframe.loc[(dataframe["throughput_up"] - dataframe["throughput_down"] > 0), 'mcs_up'].mean()
        variance_mcs_up = dataframe.loc[(dataframe["throughput_up"] - dataframe["throughput_down"] > 0), 'mcs_up'].var()

        avg_highest_rsrp = dataframe['highest_rsrp'].mean()
        variance_highest_rsrp = dataframe['highest_rsrp'].var()

        try:
            most_freq_beam = dataframe['selected_beam'].value_counts().idxmax()
        except:
            most_freq_beam = "NO SELECTED BEAM"
        if dataframe['direction'].iloc[0] == "N":
            lat = dataframe['lat'].iloc[0]
            long = dataframe['long'].iloc[0]
        new_row = {'id': n, 'direction': dataframe['direction'].iloc[0], 'lat': lat,
                   'long': long, 'avg_throughput_up': upload_mean,
                   'variance_throughput_up': upload_variance, 'avg_throughput_down': download_mean,
                   'variance_throughput_down': download_variance, 'avg_mcs_up': avg_mcs_up,
                   'variance_mcs_up': variance_mcs_up, 'avg_mcs_down': avg_mcs_down,
                   'variance_mcs_down': variance_mcs_down, 'avg_highest_rsrp': avg_highest_rsrp,
                   'variance_highest_rsrp': variance_highest_rsrp, 'most_freq_beam': most_freq_beam}
        n += 1
        new_rows_list.append(new_row)
    df = pd.DataFrame(new_rows_list, columns=columns)
    df.to_csv('averaged_out.csv', index=False)
