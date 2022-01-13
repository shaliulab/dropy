import argparse
import logging
from dropy.web_utils import sync

logger = logging.getLogger(__name__)
logging.getLogger("dropy.updown.utils").setLevel(logging.DEBUG)
logging.getLogger("dropy.updown.base").setLevel(logging.DEBUG)

def get_parser(ap=None):
    if ap is None:
        ap = argparse.ArgumentParser()

    ap.add_argument("source")
    ap.add_argument("dest")
    ap.add_argument("--skip-existing-files", action="store_true", default=False, dest="skip_existing_files")
    ap.add_argument("--recursive", action="store_true", default=False, dest="recursive")
    ap.add_argument("--ncores", default=1, type=int)
    
    return ap

def main(args=None):

    if args is None:
        ap = get_parser()
        args = ap.parse_args()

    source = args.source
    dest = args.dest
    sync(
        source, dest,
        skip_existing_files=args.skip_existing_files,
        ncores=args.ncores,
        recursive=args.recursive,
    )



if __name__ == "__main__":
    main()


#with open("AOJ_Passport.pdf", "wb") as f:
#    metadata, res = dbx.files_download(path="/Antonio/FSLLab/AOJ_Passport.pdf")
#    f.write(res.content)
