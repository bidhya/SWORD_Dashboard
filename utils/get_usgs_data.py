import os
import requests
import numpy as np
import pytz
import pandas as pd
import logging
feet2meters = 0.3048
cfs2cms = 0.02832  # TODO this is approximate


# Only to download RDB files
# Don't use JSON files for field data as they are not complete columns
# out_csv_folder = "data/usgs/velocity_csv_utc"
ida_folder = "data/usgs/ida"  # Alert: calling from notebook will create this folder relative to notebook. Clearly wrong!
os.makedirs(ida_folder, exist_ok=True)  # NEW: So site can be deployed from scratch

field_measure_folder = "data/usgs/field_measure"
os.makedirs(field_measure_folder, exist_ok=True)  # NEW: So site can be deployed from scratch


def read_usgs_ida(gage):
    """ gage: stationID of USGS gage
        Instaneous data archive  
        TODO: 
            Check this gage 03399800. It has extra two columns for backwater effect
                USGS 03399800 OHIO RIVER AT SMITHLAND DAM, SMITHLAND, KY
    """
    if os.path.exists(os.path.join(ida_folder, f'{gage}_ida.csv')):
        df = pd.read_csv(os.path.join(ida_folder, f'{gage}_ida.csv'), index_col='datetime', parse_dates=True, infer_datetime_format=True)
        return df
    download_folder = f"{ida_folder}/downloads"
    os.makedirs(download_folder, exist_ok=True)
    base_url = 'http://waterservices.usgs.gov/nwis/{data_type}/?format={output_format}&sites={sites}&startDT={startDT}&endDT={endDT}&parameterCd={parameter}'
    ida_url = base_url.format(data_type='iv', output_format='rdb', sites=gage, startDT='2010-08-01T00:00Z', endDT='2011-09-01T00:00Z', parameter='00060,00065')
    try:
        outfile = f'{download_folder}/{gage}.rdb'
        # Download the discharge from internet by calling this function
        if not os.path.isfile(outfile):
            r = requests.get(ida_url)
            if r.status_code == 200:
                with open(outfile, "wb") as code:
                    code.write(r.content)
            else:
                logging.error(f'\t{gage} \t Request code {r.status_code}')

        # df = pd.read_csv(ida_url, comment='#', sep='\t', low_memory=False)  # problem when data is large
        df = pd.read_csv(outfile, comment='#', sep='\t', low_memory=False)  # from saved rdb file
        # Message on nwis site: #  No sites found matching all criteria
        # Columns (1,4,6) have mixed types. Specify dtype option on import or set low_memory=False
        df = df.drop(0)  # first row after headers is fieldsize specification such as 5s	15s	6s..
        if len(df) > 1:
            df = df.drop(['agency_cd', 'site_no'], axis=1)
            if "EST" or "EDT" in df.tz_cd.unique():
                tz = pytz.timezone('US/Eastern')
            elif "CST" or "CDT" in df.tz_cd.unique():
                tz = pytz.timezone('US/Central')
            elif "MST" or "MDT" in df.tz_cd.unique():
                tz = pytz.timezone('US/Mountain')
            elif "PST" or "PDT" in df.tz_cd.unique():
                tz = pytz.timezone('US/Pacific')
            elif "AKST" or "AKDT" in df.tz_cd.unique():
                tz = pytz.timezone('US/Alaska')
            elif "HST" or "HDT" in df.tz_cd.unique():
                tz = pytz.timezone('US/Hawaii')
            else:
                print("Unknown timezone")
            df["datetime"] = pd.to_datetime(df.datetime)
            # df.datetime.dt.tz_localize("US/Eastern", ambiguous='infer')
            df["datetime"] = df.datetime.apply(lambda x: tz.localize(x))  # seems like daytime savings is automatically resolved
            df["datetime"] = df.datetime.dt.tz_convert("UTC")
            df.index = df.datetime
            df = df.drop(['datetime', 'tz_cd'], axis=1)
            df.columns = ["discharge", "discharge_cd", "stage", "stage_cd"]
            df = df[["discharge", "stage"]]
            df["discharge"] = df.discharge.astype("float") * cfs2cms
            df["stage"] = df.stage.astype("float") * feet2meters
            df = df.loc["2010":"2011"]

            # df = df.dropna()  # This may be required
            df.to_csv(os.path.join(ida_folder, f'{gage}_ida.csv'), index=True, header=True)
            return df
        else:
            return None
    except:
        logging.info(f"IDA: Error downloading/processing {gage}")  # mostly empty due to no field data; just html downloaded by script
        logging.info(f"\tCheck url: {ida_url}")


def read_usgs_field_data(gage):
    """ gage: stationID of USGS gage
    """
    if os.path.exists(os.path.join(field_measure_folder, f"{gage}.csv")):
        df = pd.read_csv(os.path.join(field_measure_folder, f"{gage}.csv"), index_col='measurement_dt', parse_dates=True, infer_datetime_format=True)
        return df
    download_folder = f"{field_measure_folder}/downloads"
    os.makedirs(download_folder, exist_ok=True)
    base_url = "http://waterdata.usgs.gov/nwis/measurements?site_no={}&agency_cd=USGS&format=rdb_expanded"
    field_measure_url = base_url.format(gage)
    try:
        outfile = f'{download_folder}/{gage}.rdb'
        # Download the discharge from internet by calling this function
        if not os.path.isfile(outfile):
            logging.info(f"{gage} <--Downloading  Field Measure")
            r = requests.get(field_measure_url)
            if r.status_code == 200:
                with open(outfile, "wb") as code:
                    code.write(r.content)
            else:
                logging.error(f'\t{gage} \t Request code {r.status_code}')

        # df = pd.read_csv(field_measure_url, comment='#', sep='\t')  # can fail sometimes for large data
        df = pd.read_csv(outfile, comment='#', sep='\t', low_memory=False)  # from saved rdb file
        ''' #To guard again error due to empty dataframe (may not be necessary because now we have try statement)
        if len(df) == 0:
            ## To protect against data frame that are empty, ie col names present but no data (row)
            print "Empty IDA  {}".format(outfile),
        # Drop the first row: it is data types (eg 5S, 15s etc)'''
        # print(df.head())

        df = df.drop(0)  # first row after headers is fieldsize specification such as 5s	15s	6s..
        df.index = pd.to_datetime(df.measurement_dt)
        df = df[df.discharge_va == df.chan_discharge]  # only take discharge measurements done at the one channel (not different): when only one channel, total discharge is same in channel_discharge

        flag1 = (df.measured_rating_diff == 'EXCL') | (df.measured_rating_diff == 'Excellent') | (df.measured_rating_diff == 'GOOD') | (df.measured_rating_diff == 'Good')
        flag2 = df.q_meas_used_fg == 'Yes'
        flags = flag1 & flag2
        df = df[flags]
        # # Select a subset of necessary columns
        df = df[['site_no', 'measurement_dt', 'tz_cd', 'gage_height_va', 'discharge_va', 'chan_width', 'chan_area', 'chan_velocity']]
        df = df.dropna()

        if len(df) == 0:
            logging.info(f"Empty dataframe after dropnan {gage}")
        # # Select a subset of necessary columns
        df = df[['site_no', 'gage_height_va', 'discharge_va', 'chan_width', 'chan_area', 'chan_velocity']]
        df = df.dropna()
        # Change datatype from object to float
        float_columns = ['gage_height_va', 'discharge_va', 'chan_width', 'chan_area', 'chan_velocity']
        for col in float_columns:
            df[str(col)] = df[str(col)].astype(float)
        # Some more flags for QA/QC
        # Get one valid index for good values and pass it to all dataframes
        velocity_flag = np.logical_and(df['chan_velocity'] > 0, df['chan_velocity'] < 10)
        gage_height_flag = np.logical_and(df['gage_height_va'] > 0, df['gage_height_va'] < 900)
        cfs_flag = df['discharge_va'] > 0
        width_flag = df['chan_width'] > 0
        area_flag = df['chan_area'] > 0
        df = df[velocity_flag & gage_height_flag & cfs_flag & area_flag & width_flag]
        # df = df['2001':]
        df = df.loc["2010":"2011"]
        # Drop the duplicates (ie, the ones measured the same time)
        # Seems like these measurements are taken on different branches of streams
        df = df.loc[df.index.drop_duplicates(keep=False)]
        if len(df) > 1:
            df.to_csv(os.path.join(field_measure_folder, f'{gage}.csv'), index=True, header=True)  # index_label='measurement_dt or utc_dt'
            return df
        else:
            return None
    except:
        logging.info(f"Field Measure: Error downloading/processing {gage}")  # mostly empty due to no field data; just html downloaded by script
        logging.info(f"\tCheck this url: {field_measure_url}")
