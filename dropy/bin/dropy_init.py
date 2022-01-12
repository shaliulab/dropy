import argparse
import os
import os.path
import json
import logging
import dropbox
import threading
from dropy import DropboxDownloader
from dropy.oauth.official import get_parser
from dropy.web_utils import set_server
import dropbox

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
    dbx = DropboxDownloader(
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
    # data = bottle.request.body.read()
    # data = json.loads(data)
    data = load_data(bottle)
    print(data)

    source = data.pop("source").split(":")
    dest = data.pop("dest").split(":")

    if len(source) == 2 and source[0] == "Dropbox" and len(dest) == 1:
        remote_path = source[1]
        local_path = dest[0]
        dest = "down"

        # I only want it to work on download mode
        try:
            md = dbx.dbx.files_get_metadata(
                path = remote_path
            )
        except dropbox.exceptions.ApiError:
            raise Exception (f"{remote_path} does not exist on Dropbox server")

    elif len(dest) == 2 and dest[0] == "Dropbox" and len(source) == 1:
        remote_path = dest[1]
        local_path = source[0]
        dest = "up"
     # I only want it to work in upload mode
        assert os.path.exists(local_path), "Local file does not exist"

    assert remote_path.startswith(os.path.sep)
    remote_path = remote_path.split(os.path.sep)
    folder = "/".join(remote_path[:2])
    subfolder = os.path.dirname("/".join(remote_path[2:]))
    fullname = local_path

    print(
        "Syncing "
        f" Fullname {fullname}"
        f" Folder {folder}"
        f"  Subfolder {subfolder}")

    # to download
    dbx.sync(
        fullname,
        folder,
        subfolder,
        dest=dest,
        **data
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
