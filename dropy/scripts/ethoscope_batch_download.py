import argparse
import logging
import re
import os.path
import pickle
import numpy as np
import pandas as pd
import joblib
import dropbox
from dropy import DropboxDownloader
from dropy.web_utils import sync, list_folder
from dropy.updown.utils import unnest, sanitize_path
from dropy.updown.base import sync_file
import dropy

logger = logging.getLogger(__name__)

def get_parser(ap=None):
    if ap is None:
        ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True) # "/Data/ethoscope/2022-01-04_ethoscope_data/results"
    ap.add_argument("--rootdir", required=True) # "/Data/ethoscope/2022-01-04_ethoscope_data/results"
    ap.add_argument("--metadata")
    ap.add_argument("--ncores", default=5, type=int)
    return ap


def get_machine_name(db_file):

    match = re.match(".*/(ETHOSCOPE_[0-9]{3})/.*", db_file)
    if match:
        machine_name = match.group(1)
        return machine_name
    else:
        return None

def get_date(db_file):

    match = re.match(".*/([0-9]{4}-[0-9]{2}-[0-9]{2})_[0-9]{2}-[0-9]{2}-[0-9]{2}/.*", db_file)
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

    res = list_folder(folder_display, recursive=4)
    files = res["paths"]

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
        dbfiles = match_ethoscope_metadata(dbfiles, metadata)


    if len(dbfiles) == 0:
        logger.warning("No dbfiles found matching your metadata")
        return

    dbfilenames = [dbfile.replace(folder_display, "") for dbfile in dbfiles]

    sync_args = [
        (
            sanitize_path(f"Dropbox:{folder_display}/{file}"),
            sanitize_path(os.path.join(args.rootdir, subfolder, file.lstrip("/")))
        )
        for file in dbfilenames
    ]

    if args.ncores == 1:
        for sync_arg in sync_args:
            sync(*sync_arg)
    else:
        joblib.Parallel(n_jobs=args.ncores)(
            joblib.delayed(sync)(
                *sync_arg
            )
                for sync_arg in sync_args
        )



if __name__ == "__main__":
    main()
