import os
import sys

from PyQt5 import QtWidgets

from dt_updates.update_3d import generate_ui_3d, loadfile_3d
from dt_updates.update_correction import generate_ui_correction, loadfile_correction
from dt_updates.update_interpolation import generate_ui_interpolation, loadfile_interpolation
from dt_updates.update_raw import generate_ui_raw, loadfile_raw
from scratch_reader import ScratchReader
from scratchtester_design import Ui_MainWindow
import logging
import logging.handlers

logFormatter = logging.Formatter("%(asctime)s %(levelname)s %(filename)s(%(lineno)d) %(message)s")
rootLogger = logging.getLogger()
rootLogger.level = logging.INFO

logfilename="{0}/{1}.log".format(os.path.dirname(os.path.realpath(__file__)), 'scratchtester_gui')
should_roll_over = os.path.isfile(logfilename)
fileHandler = logging.handlers.RotatingFileHandler(logfilename, mode='w', backupCount=5)
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)
if should_roll_over:  # log already exists, roll over!
    fileHandler.doRollover()

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)


class ScratchtesterUI:
    scratchReader = None

    def __init__(self):
        logging.info("Initalization")
        self.scratchReader = ScratchReader()
        if not os.path.isfile("last_opened.json"):
            with open("last_opened.json", "w+") as f:
                f.write("{}")

        self.scratchReader.options.autosave = True

        app = QtWidgets.QApplication(sys.argv)
        MainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(MainWindow)

        self.generate_ui()

        MainWindow.show()

        # ProcessRunnable(target=self.loadfile, args=("last_opened.json",)).start()
        self.loadfile("last_opened.json")

        sys.exit(app.exec_())

    def generate_ui(self):
        logging.info("Generate UI")
        generate_ui_raw(self)
        generate_ui_interpolation(self)
        generate_ui_correction(self)
        generate_ui_3d(self)

    def loadfile(self, f):
        logging.info("Load file"+f)
        self.scratchReader.open(f, read=False)
        loadfile_raw(self)
        loadfile_interpolation(self)
        loadfile_correction(self)
        loadfile_3d(self)


# python -m PyQt5.uic.pyuic scratchtester.ui -o scratchtester_design.py
# nuitka --follow-imports --standalone --plugin-enable=qt-plugins --plugin-enable=pylint-warnings --verbose scratchtester_gui.py

if __name__ == "__main__":
    try:
        ScratchtesterUI()
    except Exception as e:
        logging.exception(e)
        raise
