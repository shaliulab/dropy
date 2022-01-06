import argparse
import logging
import re
import os.path
import numpy as np
import pandas as pd
import joblib
import dropbox
from dropy import DropboxDownloader
from dropy.oauth.official import get_parser as oauth_get_parser
from dropy.web_utils import sync
import dropy

logger = logging.getLogger(__name__)

def get_parser(ap=None):
    ap = oauth_get_parser(ap)    
    ap.add_argument("--folder", required=True) # "/Data/ethoscope/2022-01-04_ethoscope_data/results"
    ap.add_argument("--rootdir", required=True) # "/Data/ethoscope/2022-01-04_ethoscope_data/results"
    ap.add_argument("--metadata")
    return ap


def unnest(input, output):
    
    for element in input:
        if isinstance(element, str):
            output.append(element)
        elif isinstance(element, list):
            unnest(element, output)
    
    return output

def get_machine_name(db_file):

    match = re.match(".*/(ETHOSCOPE_[0-9]{3})/.*", db_file)
    if match:
        machine_name = match.group(1)
        return machine_name
    else:
        return None

def get_date(db_file):

    match = re.match(".*/([0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{2}-[0-9]{2}-[0-9]{2})/.*", db_file)
    if match:
        date = match.group(1)
        return date
    else:
        return None

def match_ethoscope_metadata(dbfiles, metadata):

    matches = []

    for dbfile in dbfiles:
        machine_name = get_machine_name(dbfile)
        date = get_date(dbfile)

        hit = np.where(
            np.bitwise_and(
                machine_name == metadata["machine_name"].values,
                date == metadata["date"].values
            )
        )[0]

        if len(hit) != 0:
            matches.append(dbfile)


    return matches


def main(ap=None, args=None):

    if args is None:
        ap = get_parser(ap)
        args = ap.parse_args()

    folder_display = args.folder.replace("/./", "/")
    subfolder = args.folder.split("/./")
    if len(subfolder) == 1:
        subfolder = ""
    else:
        subfolder = subfolder[1]

    print(f"dropy will save data to {args.rootdir}/{subfolder}")

    dbx = DropboxDownloader(
        app_secret=args.app_secret,
        app_key=args.app_key,
    )
    dbx.init()

    res = dbx.list_folder(folder_display, recursive=True)
    files = res["files"]
    files = unnest(files, [])

    # files = ['/Data/ethoscope/2022-01-04_ethoscope_data/results/None.txt', '/Data/ethoscope/2022-01-04_ethoscope_data/results/None', '/Data/ethoscope/2022-01-04_ethoscope_data/results/index.txt', '/Data/ethoscope/2022-01-04_ethoscope_data/results/004aad42625f433eb4bd2b44f811738e/ETHOSCOPE_004/2021-04-14_12-19-51/2021-04-14_12-19-51_004aad42625f433eb4bd2b44f811738e.txt', '/Data/ethoscope/2022-01-04_ethoscope_data/results/004aad42625f433eb4bd2b44f811738e/ETHOSCOPE_004/2021-04-14_12-19-51/2021-04-14_12-19-51_004aad42625f433eb4bd2b44f811738e.db', '/Data/ethoscope/2022-01-04_ethoscope_data/results/004aad42625f433eb4bd2b44f811738e/ETHOSCOPE_004/2021-06-14_07-34-56/2021-06-14_07-34-56_004aad42625f433eb4bd2b44f811738e.txt', '/Data/ethoscope/2022-01-04_ethoscope_data/results/004aad42625f433eb4bd2b44f811738e/ETHOSCOPE_004/2021-06-14_07-34-56/2021-06-14_07-34-56_004aad42625f433eb4bd2b44f811738e.db', '/Data/ethoscope/2022-01-04_ethoscope_data/results/004aad42625f433eb4bd2b44f811738e/ETHOSCOPE_004/2021-06-21_15-59-47/2021-06-21_15-59-47_004aad42625f433eb4bd2b44f811738e.db', '/Data/ethoscope/2022-01-04_ethoscope_data/results/004aad42625f433eb4bd2b44f811738e/ETHOSCOPE_004/2021-06-21_15-59-47/2021-06-21_15-59-47_004aad42625f433eb4bd2b44f811738e.txt', '/Data/ethoscope/2022-01-04_ethoscope_data/results/004aad42625f433eb4bd2b44f811738e/ETHOSCOPE_004/2021-06-29_15-46-12/2021-06-29_15-46-12_004aad42625f433eb4bd2b44f811738e.txt']

    dbfiles = []
    for file in files:
        if re.match(".*.db$", file):
            dbfiles.append(file)

        
    dbfiles = sorted(dbfiles)        
    print(dbfiles)

    if args.metadata is None:
        answer = input("No metadata passed. Do you want to download every dbfile?: Y/n ")
        if answer == "Y":
            pass
        else:
            return

    else:
        metadata = pd.read_csv(args.metadata)[["machine_name", "date"]]
        metadata.drop_duplicates(inplace=True)

        import ipdb; ipdb.set_trace()

        dbfiles = match_ethoscope_metadata(dbfiles, metadata)


    if len(dbfiles) == 0:
        logger.warning("No dbfiles found matching your metadata")
        return
    
    dbfilenames = [os.path.basename(dbfile) for dbfile in dbfiles]

    joblib.Parallel(n_jobs=-2)(
        joblib.delayed(sync)(
            f"Dropbox:{folder_display}/{file}", os.path.join(args.rootdir, subfolder, file)
        )
            for file in dbfilenames
    )



if __name__ == "__main__":
    main()