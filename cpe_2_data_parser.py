import pandas as pd
import numpy as np
from IPython.display import display
import functools

pd.set_option("display.max_rows", 200)
pd.set_option('display.max_colwidth', 600)

THRG_TRESHOLD= 100 #treshold 
SPEED_TEST = 37 #seconds
BEAMS_COUNT = 8


INPUT_COLUMNS = {
    # final columns needed in the output
    "throughput_up": "PUSCH throughput (NR)",
    "throughput_down": "PDSCH throughput (NR)",
    "mcs_up": "PUSCH MCS CW0 (NR)",
    "mcs_down": "PDSCH MCS CW0 (NR)",
    "rsrp": "RSRP (NR SpCell)",
    "lat": "Latitude",
    "long": "Longitude",
    "time": "Time",

    #helpers: columns yet to be processes
    "BEAMS": "Beam index (NR SpCell)",    # the beams detected in a measurement
    "BEAM_TYPE": "Beam type (NR SpCell)", # if the beam is being used or not
}

BEAM_TYPE = "BEAM_TYPE"
BEAMS = "BEAMS"

DIRECTION_MAP = ["N", "E","S", "W"]
NEMO_BEAM_TYPES = [
    "Detected beam",  # just detected not being used,
    "Serving beam"    # main beam being used
]

output_columns = {
  "ID": "id",
  "DIR": "direction",
  "selected_beam": "selected_beam"
}

def import_csv(path):
    df = pd.read_csv(path, low_memory=False)
    #df = pd.concat([df, df_temp], ignore_index=True)
    return df

def getServingIdBeam(beam_type: str):
    return beam_type.str.split(", ").apply(
        lambda x: x.index(NEMO_BEAM_TYPES[1]) if NEMO_BEAM_TYPES[1] in x else None)

def getFirstValidItemOfSeries(series):
    series.reset_index(inplace=True,drop=True)
    first_valid_vals_index = series.apply(pd.DataFrame.first_valid_index)
    first_valid_vals_index = first_valid_vals_index.replace(np.nan, -1) # to avoid wrong indexing

    first_valid_values = pd.DataFrame(columns=series.columns) 

    test = [ series[c].iloc[int(first_valid_vals_index[c])] 
                if (first_valid_vals_index[c] != -1) else np.nan for c in series.columns ]
    first_valid_values.loc[0] = test
    return first_valid_values


def getBeamsData(x):
    init = [[0] * BEAMS_COUNT]
    if (x != -1):
        beam_array = x.split(", ")
        if len(beam_array) <= BEAMS_COUNT:
            valid_values =[beam_array + [0] * (BEAMS_COUNT- len(beam_array))] 
            return valid_values[0]
        else:
            return init[0]
    else:
        return init[0]


def parse_to_parameters(data: pd.DataFrame,file_n, file, only_download):
    df = pd.DataFrame()
    
    # GET ALL COLUMNS
    for column_id in INPUT_COLUMNS:
        columns_name = INPUT_COLUMNS[column_id]
        df[column_id] = data[columns_name]

    df.reset_index(inplace=True, drop=True)
    
    # CLEAN DATA
    # divide dataframe in miliseconds
    df["second"] = data["Time"].astype(str).apply(lambda x : x.split(":")[1].split(".")[0] ) 
    df["milisecond"] = data["Time"].astype(str).apply(lambda x : x.split(":")[2].split(".")[0] ) 

    #df = df.dropna(subset=['direction'])
    # for each milisencond take the first values of the series
    df = df.groupby(["second",'milisecond']).apply(getFirstValidItemOfSeries)
    df = df.drop(["second","milisecond"], axis=1).reset_index(drop=True)


    #########################################################################
    # get columns beam_id
    beam_ids_matrix = df[BEAMS].astype(str).apply(getBeamsData)
    DF_beams_ids = pd.DataFrame(
        beam_ids_matrix.tolist(),
        columns=["beam_id{}".format(i) for i in range(0,BEAMS_COUNT)]
    )

    # get columns beam rsrp
    beams_rsrp = df["rsrp"].fillna(-1).apply(getBeamsData)
    DF_beams_rsrp = pd.DataFrame(
        beams_rsrp.tolist(),
        columns=["rsrp{}".format(i) for i in range(0,BEAMS_COUNT)]
    )

    df = pd.concat([df, DF_beams_rsrp,DF_beams_ids], axis=1)
    df = df.drop(["rsrp"], axis=1)

    # get the selected beam
    selected_ids = df[[BEAM_TYPE]].astype(str).apply(getServingIdBeam)[BEAM_TYPE]
    selected_ids = selected_ids.fillna(-1).astype(int) # ot aboid wrong indexing
    df[BEAMS] = df[BEAMS].fillna(-1)
    df["selected_beam"] = [ df[BEAMS][i].split(",")[selected_ids[i]] 
                        if (i != -1 and df[BEAMS].loc[i] != -1 and selected_ids[i] != -1) 
                        else None 
                        for i in df.index.astype(int) ]

    # id, direction, lat, long, throughput_up, throughput_down,  mcs, rsrp1, rsp2, rsp3 (...), beam_id1, beam_2, beam_3, (...), selected_beam (modificato) 
    df = df.drop(columns=[BEAM_TYPE, BEAMS]).reset_index(drop=True)

    # generate the direction
    df["direction"] = None
        # to get cleaner results
    if not only_download:
        df = df[
            abs(df["throughput_down"] - df["throughput_up"]) >= 20
        ].copy()
    
    df.reset_index(drop=True, inplace=True)
   
    """
        Every direction is made of two phases: download and upload
        When the last range of values was downlad (lastitsDownload)
        and the current is upload (initDirectionRange)

        When a download and a upload phase has passed
        it means the direction has changed
    """
    
    if (only_download):
        df["throughput_up"] = 20# everything less than 10mbs in download is not considered
        df.loc[df["throughput_down"] <= 20, "throughput_down"] = 0

    maksThroughPutInvertion = df["throughput_down"] - df["throughput_up"]
    itsDownload = True
    lastitsDownload = False
    initDirectionRange = 0
    dic = 0 # pointer that sleect the direction
    teste = np.array([])
    

    if (only_download):
        initDirectionRange=maksThroughPutInvertion[maksThroughPutInvertion>0].index[0]
    for i, item in enumerate(maksThroughPutInvertion):
       
        if (only_download):
            itsDownload = item > 0
            if ((initDirectionRange!=i and (itsDownload and not lastitsDownload)) or (i == maksThroughPutInvertion[maksThroughPutInvertion>0].index[-1])) and (i-initDirectionRange)>5:
                

                # special harcoded cases
                if (file!="23 Oct with GPS/23Oct23 155045.1.csv" 
                    and file != "23 Oct with GPS/23Oct23 155740.1.csv"
                    ) or (
                        file=="23 Oct with GPS/23Oct23 155045.1.csv" and i!=115 and i!=116 and i!=117
                    ) or (
                        file=="23 Oct with GPS/23Oct23 155740.1.csv" and (i>65)
                    ):
                    df.loc[initDirectionRange:i-1,"direction"] = DIRECTION_MAP[dic] # iterate over the directions
                    teste = np.append(teste,[DIRECTION_MAP[dic], i-initDirectionRange])
                    dic = (dic+1) % 4
                    initDirectionRange = i
            df.loc[maksThroughPutInvertion < 0, "direction"] = None # iterate over the directions

        else:
            itsDownload = item > 0

            # triguer to change phase
            # new download phase starts 
            if initDirectionRange!=i and ((itsDownload and not lastitsDownload) or (not itsDownload and i == maksThroughPutInvertion.index[-1])):
                df.loc[initDirectionRange:i-1,"direction"] = DIRECTION_MAP[dic] # iterate over the directions
                teste = np.append(teste,[DIRECTION_MAP[dic], i-initDirectionRange])
                dic = (dic+1) % 4
                initDirectionRange = i
            
        
            
        lastitsDownload = itsDownload
        
    df = df.dropna(subset=["direction"])

    print(teste, file_n, " only download: ", only_download)
    
    # df = df.loc[
    #     ((df["direction"] == "N") & (df["throughput_down"]>100))
    #     | (df["direction"] != "N")]
    #df = df.dropna(subset=["direction"]).reset_index(drop=True)
    df = df[0:-2]

    if (only_download):
        df["throughput_up"] = 0
    df["file"] = file
    df["only_download"] = only_download
    
    # order columns
    return df[["file", "only_download","direction","throughput_up","throughput_down","lat","long","mcs_up","mcs_down","rsrp0","rsrp1","rsrp2","rsrp3","rsrp4","rsrp5","rsrp6","rsrp7","beam_id0","beam_id1","beam_id2","beam_id3","beam_id4","beam_id5","beam_id6","beam_id7","selected_beam"]]

if __name__ == '__main__':

    files = [
        ["20 Oct with GPS/23Oct20 170308.1.csv",False],
        ["20 Oct with GPS/23Oct20 171114.1.csv",False],
        ["20 Oct with GPS/23Oct20 174229.1.csv",True],
         ["23 Oct with GPS/23Oct23 120535.1.csv",False],
         ["23 Oct with GPS/23Oct23 124506.1.csv",False],
         ["23 Oct with GPS/23Oct23 151921.1.csv",False],
        ["23 Oct with GPS/23Oct23 152439.1.csv",True],
         ["23 Oct with GPS/23Oct23 153640.1.csv",False],
         #["23 Oct with GPS/23Oct23 154207.1.csv",False],
        ["23 Oct with GPS/23Oct23 155045.1.csv",True],
        ["23 Oct with GPS/23Oct23 155740.1.csv",True],
            #["23 Oct with GPS/23Oct23 160227.1.csv",True],
            #["23 Oct with GPS/23Oct23 165852.1.csv",True],
            #["23 Oct with GPS/23Oct23 170908.1.csv",True],
            #["23 Oct with GPS/23Oct23 171642.1.csv",True],
            #["25 Oct with GPS/23Oct25 153250.1.csv",True],
            #["25 Oct with GPS/23Oct25 154203.1.csv",True],
         ["25 Oct with GPS/23Oct25 160340.1.csv",False],
         ["25 Oct with GPS/23Oct25 160839.1.csv",False],
         ["25 Oct with GPS/23Oct25 162002.1.csv",False],
         ["25 Oct with GPS/23Oct25 163010.1.csv",False],
         ["25 Oct with GPS/23Oct25 163415.1.csv",True],
            #["25 Oct with GPS/23Oct25 163957.1.csv",True]
    ]


    df = pd.DataFrame()
    for i, file in enumerate(files):
        [file, only_download] = file
        data = import_csv("./Nemo_toParse/"+file)
         
        print("NEW FILE", file)
        filtered_df = parse_to_parameters(data, i,file,only_download)
        if i==0:
            filtered_df.to_csv('filtered_out.csv')
        else:
            filtered_df.to_csv('filtered_out.csv',mode='a', header=False)
        
        