import argparse
import logging
from dropy import DropboxDownloader

logger = logging.getLogger(__name__)

def get_parser():

    ap = argparse.ArgumentParser()
    ap.add_argument("--fullname", required=True)
    ap.add_argument("--folder", required=True)
    ap.add_argument("--subfolder", required=True)
    return ap

def main(args=None):

    if args is None:
        ap = get_parser()
        args = ap.parse_args()


    dbx = DropboxDownloader()
    dbx.init()

    # to download
    dbx.sync_file(
        args.fullname,
        args.folder,
        args.subfolder,
    )
    
    dbx.close()



if __name__ == "__main__":
    main()


#with open("AOJ_Passport.pdf", "wb") as f:
#    metadata, res = dbx.files_download(path="/Antonio/FSLLab/AOJ_Passport.pdf")
#    f.write(res.content)
