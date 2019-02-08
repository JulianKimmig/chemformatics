import logging
import os
from qtpy import QtCore
from dt_updates.sidefunctions import PandasModel, openFileNameDialog
from dt_updates.update_interpolation import loadfile_interpolation


def loadfile_raw(sr):
    logging.info("laod raw")
    sr.ui.raw_file_path.setText(sr.scratchReader.raw_file)
    model = PandasModel(sr.scratchReader.read_raw())
    sr.ui.rawdatatable.setModel(model)

    sr.ui.raw_x_fac.setValue(
        sr.scratchReader.options.get("measurement", "x_fac", default=1)
    )
    sr.ui.raw_y_fac.setValue(
        sr.scratchReader.options.get("measurement", "y_fac", default=1)
    )
    sr.ui.raw_z_fac.setValue(
        sr.scratchReader.options.get("measurement", "z_fac", default=1)
    )

    index = sr.ui.raw_data_sep.findText(
        sr.scratchReader.raw_data_separator.encode("unicode_escape").decode("utf-8"),
        QtCore.Qt.MatchFixedString,
    )
    if index >= 0:
        sr.ui.raw_data_sep.setCurrentIndex(index)

    index = sr.ui.raw_data_struc.findText(
        sr.scratchReader.raw_data_structure, QtCore.Qt.MatchFixedString
    )
    if index >= 0:
        sr.ui.raw_data_struc.setCurrentIndex(index)


def generate_ui_raw(sr):
    logging.info("generate raw")

    def open_raw_file():
        try:
            fp = os.path.dirname(
                os.path.abspath(
                    sr.scratchReader.options.get("data", "raw", "path", default=None)
                )
            )
        except:
            fp = ""
        fn = openFileNameDialog("open raw data", fp)
        if fn:
            sr.ui.raw_file_path.setText(fn)

    def load_raw_file():
        t = sr.ui.raw_file_path.text()
        if os.path.isfile(t):
            sr.scratchReader.options.put(
                "measurement", "x_fac", value=sr.ui.raw_x_fac.value()
            )
            sr.scratchReader.options.put(
                "measurement", "y_fac", value=sr.ui.raw_y_fac.value()
            )
            sr.scratchReader.options.put(
                "measurement", "z_fac", value=sr.ui.raw_z_fac.value()
            )

            sr.scratchReader.raw_file = t
            loadfile_raw(sr)
            loadfile_interpolation(sr)

    def change_raw_sep(sep):
        x = sep.encode("utf-8").decode("unicode_escape")
        if x != sr.scratchReader.raw_data_separator:
            sr.scratchReader.raw_data_separator = x

    def change_raw_struc(struc):
        if struc != sr.scratchReader.raw_data_structure:
            sr.scratchReader.raw_data_structure = struc

    sr.ui.raw_search_button.clicked.connect(open_raw_file)
    sr.ui.raw_load_button.clicked.connect(load_raw_file)

    for item in sr.scratchReader.available_separators:
        x = item.encode("unicode_escape").decode(
            "utf-8"
        )  #''.join([c.encode('unicode_escape').decode('utf-8') for c in item])
        sr.ui.raw_data_sep.addItem(x)
    sr.ui.raw_data_sep.activated[str].connect(change_raw_sep)

    for item in sr.scratchReader.available_raw_structs:
        sr.ui.raw_data_struc.addItem(item)
    sr.ui.raw_data_struc.activated[str].connect(change_raw_struc)
