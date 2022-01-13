import argparse
import logging
from dropy import DropboxHandler
from dropy.oauth.official import get_parser as get_oauth_parser
logger = logging.getLogger(__name__)
logging.getLogger("dropy.updown.utils").setLevel(logging.DEBUG)
logging.getLogger("dropy.updown.base").setLevel(logging.DEBUG)

def get_parser(ap=None):
    ap = get_oauth_parser(ap)
    ap.add_argument("--fullname", required=True)
    ap.add_argument("--folder", required=True)
    ap.add_argument("--subfolder", required=True)
    return ap

def main(args=None):

    if args is None:
        ap = get_parser()
        args = ap.parse_args()


    dbx = DropboxHandler(
        app_key=args.app_key,
        app_secret=args.app_secret
    )

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
