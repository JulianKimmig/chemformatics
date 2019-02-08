import logging
import os
import pandas
from qtpy import QtCore
from dt_updates import update_correction
from dt_updates.sidefunctions import PandasModel, saveFileNameDialog


def loadfile_interpolation(sr):
    logging.info("load interpolation")
    sr.ui.interpolation_resolution_x.setValue(
        sr.scratchReader.interpolation_resolution[0]
    )
    sr.ui.interpolation_resolution_y.setValue(
        sr.scratchReader.interpolation_resolution[1]
    )

    index = sr.ui.interpolation_method.findText(
        sr.scratchReader.interpolation_method, QtCore.Qt.MatchFixedString
    )
    if index >= 0:
        sr.ui.interpolation_method.setCurrentIndex(index)

    if sr.scratchReader.Z.size > 4:
        model = PandasModel(
            pandas.DataFrame(
                sr.scratchReader.Z, index=sr.scratchReader.y, columns=sr.scratchReader.x
            )
        )
        sr.ui.interpolation_data_table.setModel(model)
        update_correction.setTopImage(sr)


def generate_ui_interpolation(sr):
    logging.info("generate inpterpolation")

    def change_interpolation_method(m):
        if m != sr.scratchReader.interpolation_method:
            sr.scratchReader.interpolation_method = m

    for item in sr.scratchReader.available_interpolation_methods:
        sr.ui.interpolation_method.addItem(item)
    sr.ui.interpolation_method.activated[str].connect(change_interpolation_method)

    def change_interpolation_resolution():
        val = [
            sr.ui.interpolation_resolution_x.value(),
            sr.ui.interpolation_resolution_y.value(),
        ]
        if val != sr.scratchReader.interpolation_resolution:
            sr.scratchReader.interpolation_resolution = val

    sr.ui.interpolation_resolution_y.valueChanged.connect(
        change_interpolation_resolution
    )
    sr.ui.interpolation_resolution_x.valueChanged.connect(
        change_interpolation_resolution
    )

    def interpolate():
        sr.scratchReader.interpolate()
        loadfile_interpolation(sr)

    sr.ui.interpolation_interpolate.clicked.connect(interpolate)

    def interpolation_save():
        if sr.scratchReader.Z.size < 4:
            return
        rawpath = sr.scratchReader.options.get("data", "raw", "path", default=None)
        expath = sr.scratchReader.options.get(
            "data", "interpolated", "path", default=None
        )
        try:
            rawpath = rawpath.rsplit(".", 1)
            rawpath = rawpath[0] + "_interpolated.csv"
        except:
            pass
        try:
            if rawpath is not None:
                fp = os.path.abspath(rawpath)
            else:
                fp = expath
        except:
            try:
                fp = expath
            except:
                fp = ""
        fn = saveFileNameDialog("open raw data", fp, "Text files (*.txt *.TXT *.csv)")
        if fn:
            sr.scratchReader.save_interpolated(fn)

    sr.ui.interpolation_save.clicked.connect(interpolation_save)
