import argparse
import os.path
import logging
import dropbox
from dropy import DropboxDownloader
from dropy.oauth.official import get_parser
import ipdb

logger = logging.getLogger(__name__)
logging.getLogger("dropy.updown.utils").setLevel(logging.DEBUG)
logging.getLogger("dropy.updown.base").setLevel(logging.DEBUG)


def main(ap=None, args=None):

    if args is None:
        ap = get_parser(ap)
        args = ap.parse_args()


    dbx = DropboxDownloader(
        app_key=args.app_key,
        app_secret=args.app_secret
    )

    dbx.init()
    ipdb.set_trace()
    dbx.close()


if __name__ == "__main__":
    main()


#with open("AOJ_Passport.pdf", "wb") as f:
#    metadata, res = dbx.files_download(path="/Antonio/FSLLab/AOJ_Passport.pdf")
#    f.write(res.content)
