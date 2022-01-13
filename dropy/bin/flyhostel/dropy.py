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