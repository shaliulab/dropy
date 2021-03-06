import os.path
import logging
import datetime
import time
import dropbox
import tqdm
from .utils import stopwatch, format_path

logger = logging.getLogger(__name__)

def download_shared_(dbx, folder, subfolder, name):

    path = format_path(
        '%s/%s' % (subfolder.replace(os.path.sep, '/'), name)
    )

    with stopwatch('download', None, None):
        try:
            md, res = dbx.sharing_get_shared_link_file(
                url = folder,
                path = path
            )
        except dropbox.exceptions.HttpError as err:
            logger.warning('*** HTTP error', err)
            return None
    data = res.content
    logger.info(len(data), 'bytes')
    logger.debug('md:', md)
    return data



def download_(dbx, folder, subfolder, name):
    """
    Download a file existing in Dropbox under `os.path.join(folder, subfolder, name)`


    Arguments:
        folder (str):
        subfolder (str):
        name (str):


    Return:
        Bytes of the file, or None if the file does not exist.
    """

    path = format_path(
        '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    )

    with stopwatch('download', os.path.join(folder, subfolder), name):
        try:
            md, res = dbx.files_download(path)

        except dropbox.exceptions.HttpError as err:
            logger.warning('*** HTTP error', err)
            return None

        except dropbox.exceptions.ApiError as err:
            import ipdb; ipdb.set_trace()

        except Exception as err:
            import ipdb; ipdb.set_trace()

        else:
            logger.info(f"{name} occupies {round(md.size/(1024**2), 2)} MiB. The download may take a while if this number is big")
            data = res.content
            logger.info(len(data), 'bytes')
            logger.debug('md:', md)
            return data

        return None


def download(dbx, folder, subfolder, name, shared=False):

    if shared:
        return download_shared_(dbx, folder, subfolder, name)
    else:
        return download_(dbx, folder, subfolder, name)



def get_current_percents(f, file_size):
    return int(100 * (f.tell() / file_size))


def upload_(dbx, fullname, folder, subfolder, name, overwrite=False):

    file_path = fullname

    f = open(file_path, "rb", buffering=0)
    file_size = os.path.getsize(file_path)

    CHUNK_SIZE = 140 * 1024 * 1024

    dest_path = format_path(
        '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
    )

    if file_size <= CHUNK_SIZE:
        dbx.files_upload(f.read(), dest_path)
    else:
        upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
        cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                offset=f.tell())
        commit = dropbox.files.CommitInfo(path=dest_path)

        pbar = tqdm.tqdm(total=100, desc="Progress %")

        while f.tell() < file_size:
            if ((file_size - f.tell()) <= CHUNK_SIZE):
                dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                cursor,
                                                commit)
            else:
                dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                cursor.session_id,
                                                cursor.offset)
                cursor.offset = f.tell()

            cur_perc = get_current_percents(f, file_size)
            pbar.update(cur_perc - pbar.n)

    f.close()

def upload_small(dbx, fullname, folder, subfolder, name, overwrite=False):

        path = format_path(
            '/%s/%s/%s' % (folder, subfolder.replace(os.path.sep, '/'), name)
        )

        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        mtime = os.path.getmtime(fullname)
        with open(fullname, 'rb') as f:
            data = f.read()
        with stopwatch('upload %d bytes' % len(data), None, None):
            try:
                res = dbx.files_upload(
                    data, path, mode,
                    client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                    mute=True)
            except dropbox.exceptions.ApiError as err:
                logger.warning('*** API error', err)
                return None
        logger.info('uploaded as', res.name.encode('utf8'))
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
