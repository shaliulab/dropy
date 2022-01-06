import argparse
import re
import pandas as pd
import dropbox
from dropy import DropboxDownloader
from dropy.oauth.official import get_parser as oauth_get_parser
import dropy

def get_parser(ap=None):

    if ap is None:
        ap = argparse.ArgumentParser()
    
    ap.add_argument("--folder", required=True) # "/Data/ethoscope/2022-01-04_ethoscope_data/results"


def unnest(input, output):
    
    for element in input:
        if element is str:
            output.append(element)
        else:
            output.extend(unnest(element, output))
    
    return output




def main(ap=None, args=None):

    if args is None:
        ap = get_parser(ap)
        args = ap.parse_args()


    dbx = DropboxDownloader(
        app_secret=args.app_secret
        app_key=args.app_key,
    )

    res = dbx.list_folder(args.folder, recursive=True)
    files = res["files"]
    files = unnest(files, [])
    dbfiles = []

    for file in files:
        if re.match("*.db$", file):
            dbfiles.append(file)
        
    print(dbfiles)



