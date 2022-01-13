"""

The flyhostel directory has the following structure

| YYYY-mm-dd_HH_MM_SS_ROI_X/
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/metadata.yaml
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/000000.npz
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/000000.extra.json (optional)
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/000000.png
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/000000.avi
...
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/lowres/ (optional)
    |-- YYYY-mm-dd_HH_MM_SS_ROI_X/lowres/metadata.yaml
    |-- YYYY-mm-dd_HH_MM_SS_ROI_X/lowres/000000.npz
    |-- YYYY-mm-dd_HH_MM_SS_ROI_X/lowres/000000.extra.json (optional)
    |-- YYYY-mm-dd_HH_MM_SS_ROI_X/lowres/000000.png
    |-- YYYY-mm-dd_HH_MM_SS_ROI_X/lowres/000000.avi
...
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/idtrackerai/
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/idtrackerai/session_000000/
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/idtrackerai/session_000000_error.txt
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/idtrackerai/session_000000_output.txt
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/idtrackerai/session_000000.sh
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/idtrackerai/session_000000-local_settings.py
...
|-- YYYY-mm-dd_HH_MM_SS_ROI_X/output/
"""
import argparse
import os.path
import logging
import joblib
from dropy.constants import DROPBOX_PREFIX, REMOTE_SEP
from dropy.web_utils import sync

logger = logging.getLogger(__name__)

def get_parser(ap=None):

    if ap is None:
        ap = argparse.ArgumentParser()
    
    ap.add_argument("--folder", required=True)
    ap.add_argument("--rootdir", required=True)
    ap.add_argument("--interval", required=True, nargs="+", type=int)
    ap.add_argument("--version", required=False, default=2, type=int)
    ap.add_argument("--ncores", required=False, default=1, type=int)
    ap.add_argument("--include-output", dest="include_output", action="store_true", default=False)
    ap.add_argument("--include-idtrackerai", dest="include_idtrackerai",  action="store_true", default=False)
    ap.add_argument("--include-imgstore", dest="include_imgstore",  action="store_true", default=False)
    return ap
    

def build_session_paths(folder, i, version):
    remote_files = []
    
    if version == 1:
        pass
    elif version == 2:
        folder = os.path.join(folder, "idtrackerai")

    remote_files.extend([
        os.path.join(folder, f"session_{str(i).zfill(6)}"),
        os.path.join(folder, f"session_{str(i).zfill(6)}_error.txt"),
        os.path.join(folder, f"session_{str(i).zfill(6)}_output.txt"),
        os.path.join(folder, f"session_{str(i).zfill(6)}.sh"),
        os.path.join(folder, f"session_{str(i).zfill(6)}-local_settings.py"),
    ])

    return remote_files

def build_paths(
    folder, rootdir, interval, version=2,
    include_output=True, include_idtrackerai=True,
    include_imgstore=True,
):

    import ipdb; ipdb.set_trace()

    remote_files = [
        os.path.join(folder, "metadata.yaml"),
    ]

    if include_output:
        
        remote_files.append(os.path.join(folder, "output"))

    
    for i in range(*interval):

        if include_imgstore:
            remote_files.extend([
                os.path.join(folder, f"{str(i).zfill(6)}.avi"),
                os.path.join(folder, f"{str(i).zfill(6)}.npz"),
                os.path.join(folder, f"{str(i).zfill(6)}.extra.json"),
                os.path.join(folder, f"{str(i).zfill(6)}.png"),
            ])

        if include_idtrackerai:

            remote_files.extend(
                build_session_paths(folder, i, version=version)
            )

    local_files = [e.replace(folder, rootdir) for e in remote_files]

    return remote_files, local_files

def sync_safe(*args, **kwargs):

    try:
        return sync(*args, **kwargs)

    except Exception as error:
        logger.warning(error)

    return None

def sync_files(remote, local, ncores=1, skip_existing_files=True):

    if ncores == 1:
    
        for i in range(len(remote)):

            sync_safe(
               f"{DROPBOX_PREFIX}{REMOTE_SEP}{remote[i]}", local[i],
                skip_existing_files=skip_existing_files,
                recursive=True
            )
        
    else:
        joblib.Parallel(n_jobs=ncores)(
            joblib.delayed(sync_safe)(
                f"{DROPBOX_PREFIX}{REMOTE_SEP}{remote[i]}", local[i],
                skip_existing_files=skip_existing_files,
                recursive=True                
            )
            for i in range(len(remote))
        )    

def main(ap=None, args=None):

    if args is None:
        ap = get_parser(ap)
        args = ap.parse_args()

    kwargs = vars(args)
    ncores = kwargs.pop("ncores")

    remote_files, local_files = build_paths(
        **kwargs
    )

    import ipdb; ipdb.set_trace()

    sync_files(remote_files, local_files, ncores)


if __name__ == "__main__":
    main()