import argparse
import os
import os.path
import json
import logging
import dropbox
import threading
from dropy import DropboxHandler
from dropy.oauth.official import get_parser
from dropy.web_utils import set_server, format_to_dropbox_api
from dropy.constants import DROPBOX_PREFIX, REMOTE_SEP
from dropy.upload import upload_folder
from dropy.updown.updown import upload

logger = logging.getLogger(__name__)
logging.getLogger("dropy.updown.utils").setLevel(logging.DEBUG)
logging.getLogger("dropy.updown.base").setLevel(logging.DEBUG)
logging.getLogger("dropy").setLevel(logging.DEBUG)

DEBUG = True
PORT = 9000
api, bottle, server = set_server(host="0.0.0.0", port=PORT)

def main(ap=None, args=None):

    if args is None:
        ap = get_parser(ap)
        args = ap.parse_args()

    global dbx
    dbx = DropboxHandler(
        app_key=args.app_key,
        app_secret=args.app_secret
    )

    dbx.init()
    bottle.run(api, host='0.0.0.0', port=PORT, debug=DEBUG, server=server)


def load_data(bottle):
    data = bottle.request.body.read()
    data = json.loads(data)
    return data

@api.post("/sync")
def sync():
    """Process the requested data and sync with Dropbox accordingly 
    
    """
    data = load_data(bottle)
    fullname, folder, subfolder, direction = format_to_dropbox_api(
        dbx,
        data.pop("source"),
        data.pop("dest"),
    )

    if direction == "down":

        # to download
        dbx.sync(
            fullname,
            folder,
            subfolder,
            direction=direction,
            **data
        )
    
    elif direction == "up":
        if os.path.isdir(fullname):
            upload_folder(
                dbx.dbx,
                fullname,
                folder,
                subfolder=subfolder,
            )
        
        elif os.path.isfile(fullname):

            upload(
                dbx.dbx,
                fullname,
                folder=folder,
                subfolder=subfolder,
                name=os.path.basename(fullname),
                overwrite=True,
                shared=False
            )




@api.post("/list_folder")
def list_folder():

    data = load_data(bottle)
    res = dbx.list_folder(**data)
    return res

@api.post("/path_exists")
def path_exists():
    data = load_data(bottle)

    try:
        md = dbx.get_metadata(
           data["path"]
        )
        if isinstance(md, dropbox.files.FileMetadata):
            return {data["path"]: True}
        elif isinstance(md, dropbox.files.FolderMetadata):
            return {data["path"]: True}

    except:
        return {data["path"]: False}
    

@api.get("/info")
def info():
    return dbx.current_account.__str__()


@api.get("/close")
def close(exit_status=0):
    logger.info("Closing...")
    dbx.close()
    os._exit(exit_status)

class BackgroundDropy(threading.Thread):

    def __init__(self, credentials, *args, name="dropy", daemon=True, **kwargs):
        self._credentials = credentials
        kwargs.update({"daemon": daemon, "name": name})
        super().__init__(*args, **kwargs)

    def run(self):

        print(self._credentials)

        main(ap=None, args=argparse.Namespace(
            **self._credentials,
            )
        )

if __name__ == "__main__":
    main()
