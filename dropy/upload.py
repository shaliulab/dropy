import os.path
from dropy.updown.updown import upload


def upload_folder(dbx, fullname, folder, subfolder):

    assert os.path.isdir(fullname)
    assert "/./" in fullname

    dir = fullname.rstrip("/")
    if dir.endswith("/."):
        mirrored_folder = ""
    else:
        _, mirrored_folder = dir.split("/./")

    for root, dirs, files in os.walk(fullname):
        for name in files:
            upload(
                dbx,
                os.path.join(root, name),
                folder=folder,
                # subfolder=mirrored_folder,
                subfolder=os.path.join(subfolder, mirrored_folder, root.replace(fullname, "").lstrip("/")),
                name=name,
                overwrite=True,
                shared=False
            )
