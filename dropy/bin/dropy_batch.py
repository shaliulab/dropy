import argparse
import os.path
import logging
import dropbox
from dropy import DropboxHandler
from dropy.oauth.official import get_parser as get_oauth_parser

logger = logging.getLogger(__name__)
logging.getLogger("dropy.updown.utils").setLevel(logging.DEBUG)
logging.getLogger("dropy.updown.base").setLevel(logging.DEBUG)

def get_parser(ap=None):
    ap = get_oauth_parser(ap)
    ap.add_argument("source")
    ap.add_argument("dest")
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


    source = args.source.split(":")
    dest = args.dest.split(":")

    if len(source) == 2 and source[0] == "Dropbox" and len(dest) == 1:
        remote_path = source[1]
        local_path = dest[0]

        # I only want it to work on download mode
        try:
            md = dbx.dbx.files_get_metadata(
                path = remote_path
            )
        except dropbox.exceptions.ApiError:
            raise Exception ("Remote file does not exist")

    elif len(dest) == 2 and dest[0] == "Dropbox" and len(source) == 1:
        remote_path = dest[1]
        local_path = source[0]
        # I only want it to work in upload mode
        assert os.path.exists(local_path), "Local file does not exist"
    
    assert remote_path.startswith(os.path.sep)
    remote_path = remote_path.split(os.path.sep)
    folder = "/".join(remote_path[:2])
    subfolder = os.path.dirname("/".join(remote_path[2:]))
    fullname = local_path


    # to download
    dbx.sync_file(
        fullname,
        folder,
        subfolder,
    )
    
    dbx.close()


if __name__ == "__main__":
    main()


#with open("AOJ_Passport.pdf", "wb") as f:
#    metadata, res = dbx.files_download(path="/Antonio/FSLLab/AOJ_Passport.pdf")
#    f.write(res.content)
