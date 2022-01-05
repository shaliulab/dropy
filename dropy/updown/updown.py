import os.path
import datetime
import time
import dropbox
from .utils import stopwatch, format_path


def download_shared_(dbx, folder, subfolder, name):

    path = format_path(
        '%s/%s' % (subfolder.replace(os.path.sep, '/'), name)
    )

    with stopwatch('download'):
        try:
            md, res = dbx.sharing_get_shared_link_file(
                url = folder,
                path = path
            )
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
    data = res.content
    print(len(data), 'bytes; md:', md)
    return data
    


def download_(dbx, folder, subfolder, name):
    """Download a file.

    Return the bytes of the file, or None if it doesn't exist.
    """

    path = format_path(
        '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    )

    with stopwatch('download'):
        try:
            md, res = dbx.files_download(path)
        except dropbox.exceptions.HttpError as err:
            print('*** HTTP error', err)
            return None
    data = res.content
    print(len(data), 'bytes; md:', md)
    return data


def download(dbx, folder, subfolder, name, shared=False):

    if shared:
        return download_shared_(dbx, folder, subfolder, name)
    else:
        return download_(dbx, folder, subfolder, name)



def upload_(dbx, fullname, folder, subfolder, name, overwrite=False):
        path = format_path(
            '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
        )

        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        mtime = os.path.getmtime(fullname)
        with open(fullname, 'rb') as f:
            data = f.read()
        with stopwatch('upload %d bytes' % len(data)):
            try:
                res = dbx.files_upload(
                    data, path, mode,
                    client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                    mute=True)
            except dropbox.exceptions.ApiError as err:
                print('*** API error', err)
                return None
        print('uploaded as', res.name.encode('utf8'))
        return res

def upload_shared_(dbx, fullname, folder, subfolder, name, overwrite=False):
    raise NotImplementedError


def upload(dbx, fullname, folder, subfolder, name, overwrite=False, shared=False):
    """Upload a file.

    Return the request response, or None in case of error.
    """

    if shared:
        return upload_shared_(dbx, fullname, folder, subfolder, name, overwrite=overwrite)
    else:
        return upload_(dbx, fullname, folder, subfolder, name, overwrite=overwrite)
