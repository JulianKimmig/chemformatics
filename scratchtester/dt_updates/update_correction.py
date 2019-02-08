import logging
from PyQt5.QtWidgets import QTableWidgetItem, QHBoxLayout
from qtpy import QtWidgets
from dt_updates.sidefunctions import FigureCanvas2D


def loadfile_correction(sr):
    logging.info("load correction")
    raw_image_type = sr.scratchReader.options.get(
        "correction", "raw_image", "type", default="mesh"
    )
    sr.ui.correction_spin_cut_upper.setValue(
        100
        * sr.scratchReader.options.get(
            *["data", "correction", "cut", "upper"], default=0.05
        )
    )
    sr.ui.correction_spin_cut_lower.setValue(
        100
        * sr.scratchReader.options.get(
            *["data", "correction", "cut", "lower"], default=0.05
        )
    )

    if raw_image_type == "mesh":
        sr.ui.correction_raw_plottype_mesh.setChecked(True)
    if raw_image_type == "contour":
        sr.ui.correction_raw_plottype_contour.setChecked(True)

    for p in sr.scratchReader.correction_points:
        add_correction_point(sr, p[0], p[1], p[2], replot=False)
    sr.correction_raw_image_canvas.plot()

    update_surf(sr)


def delrow_by_col_item(sr, col, refitem):
    for i in range(sr.ui.correntionpoint_table.rowCount()):
        d = sr.ui.correntionpoint_table.cellWidget(i, col)
        if d == refitem:
            sr.ui.correntionpoint_table.removeRow(i)
            return


def add_correction_point(sr, x, y, z, replot=True):
    row = 0
    sr.ui.correntionpoint_table.insertRow(row)
    point = sr.correction_raw_image_canvas.addPoint(x, y, z, replot=replot)
    sr.ui.correntionpoint_table.setItem(row, 0, QTableWidgetItem(str(x)))
    sr.ui.correntionpoint_table.setItem(row, 1, QTableWidgetItem(str(y)))
    sr.ui.correntionpoint_table.setItem(row, 2, QTableWidgetItem(str(z)))
    del_button = QtWidgets.QPushButton()
    del_button.setText("remove")
    pWidget = QtWidgets.QWidget()
    pLayout = QHBoxLayout(pWidget)
    pWidget.layout().addWidget(del_button)
    pLayout.addWidget(del_button)
    pLayout.setContentsMargins(0, 0, 0, 0)
    pWidget.setLayout(pLayout)

    sr.ui.correntionpoint_table.setCellWidget(row, 3, pWidget)

    def rmP():
        sr.correction_raw_image_canvas.removePoint(point)
        delrow_by_col_item(sr, 3, pWidget)

    del_button.clicked.connect(rmP)


def update_surf(sr):
    lower_perc = sr.ui.correction_spin_cut_lower.value()
    upper_perc = sr.ui.correction_spin_cut_upper.value()

    sr.scratchReader.calculate_correction_surface(
        cut_upper=upper_perc / 100, cut_lower=lower_perc / 100
    )
    update_correction_surface(sr)


def generate_ui_correction(sr):
    logging.info("generate correction")
    static_canvas = FigureCanvas2D(sr.ui.coorection_top_image_widget)
    sr.ui.coorection_top_image_widget.layout().addWidget(static_canvas)

    sr.ui.update_correction_button.clicked.connect(lambda: update_surf(sr))

    def new_addPoint(x, y, z, replot=True):
        p = static_canvas.old_addPoint(x, y, z, replot=replot)
        sr.scratchReader.add_correction_point(p.x, p.y, p.z)
        return p

    static_canvas.old_addPoint = static_canvas.addPoint
    static_canvas.addPoint = new_addPoint

    def new_removePoint(p, replot=True):
        logging.info("remove correctionpoint")
        p = static_canvas.old_removePoint(p, replot=replot)
        sr.scratchReader.remove_correction_point(p.x, p.y)
        return p

    static_canvas.old_removePoint = static_canvas.removePoint
    static_canvas.removePoint = new_removePoint

    def set_raw_plot_type(button):
        if button.isChecked():
            if button == sr.ui.correction_raw_plottype_contour:
                static_canvas.set_surfaceType("contour")
                sr.scratchReader.options.put(
                    "correction", "raw_image", "type", value="contour"
                )
            if button == sr.ui.correction_raw_plottype_mesh:
                static_canvas.set_surfaceType("mesh")
                sr.scratchReader.options.put(
                    "correction", "raw_image", "type", value="mesh"
                )

    sr.ui.correction_raw_plottype_mesh.setChecked(True)
    sr.ui.correction_raw_plottype_contour.toggled.connect(
        lambda: set_raw_plot_type(sr.ui.correction_raw_plottype_contour)
    )
    sr.ui.correction_raw_plottype_mesh.toggled.connect(
        lambda: set_raw_plot_type(sr.ui.correction_raw_plottype_mesh)
    )

    sr.ui.correntionpoint_table.setColumnCount(4)
    sr.ui.correntionpoint_table.setHorizontalHeaderLabels(["x", "y", "z", "del"])

    def callback(event):
        x = event.xdata
        y = event.ydata
        if (
            x is not None
            and y is not None
            and sr.scratchReader.Z.size > 1
        ):
            z = sr.scratchReader.get_z(x, y)
            add_correction_point(sr, x, y, z)

    static_canvas.callbacks.connect("button_press_event", callback)

    sr.correction_raw_image_canvas = static_canvas

    correction_surface = FigureCanvas2D(sr.ui.correction_surface_view)
    sr.ui.correction_surface_view.layout().addWidget(correction_surface)
    sr.correction_surface = correction_surface

    correcte_data_plot = FigureCanvas2D(sr.ui.correcte_data_plot)
    sr.ui.correcte_data_plot.layout().addWidget(correcte_data_plot)
    sr.correcte_data_plot = correcte_data_plot

    def addcorner():
        if sr.scratchReader.X.size < 2 and sr.scratchReader.Y.size < 2:
            return

        # try:
        add_correction_point(
            sr,
            x=sr.scratchReader.X[0][0],
            y=sr.scratchReader.Y[0][0],
            z=sr.scratchReader.Z[0][0],
            replot=False,
        )
        add_correction_point(
            sr,
            x=sr.scratchReader.X[-1][0],
            y=sr.scratchReader.Y[-1][0],
            z=sr.scratchReader.Z[-1][0],
            replot=False,
        )
        add_correction_point(
            sr,
            x=sr.scratchReader.X[0][-1],
            y=sr.scratchReader.Y[0][-1],
            z=sr.scratchReader.Z[0][-1],
            replot=False,
        )
        add_correction_point(
            sr,
            x=sr.scratchReader.X[-1][-1],
            y=sr.scratchReader.Y[-1][-1],
            z=sr.scratchReader.Z[-1][-1],
        )

    # except:
    #    pass
    sr.ui.interpolation_addcorner_button.clicked.connect(addcorner)

    def clear():
        for p in static_canvas.points:
            sr.correction_raw_image_canvas.removePoint(p, False)
        sr.correction_raw_image_canvas.plot()
        sr.ui.correntionpoint_table.setRowCount(0)

    sr.ui.interpolation_clear_button.clicked.connect(clear)


def setTopImage(sr):
    logging.info("set correction rar image")
    Z = sr.scratchReader.Z
    X = sr.scratchReader.X
    Y = sr.scratchReader.Y
    sr.correction_raw_image_canvas.plot_surface(X, Y, Z)


def update_correction_surface(sr):
    logging.info("update correction surface")
    if sr.scratchReader.correction_surface is not None:
        Z = sr.scratchReader.correction_surface
        X = sr.scratchReader.X
        Y = sr.scratchReader.Y
        sr.correction_surface.plot_surface(X, Y, Z)

        Z = sr.scratchReader.corrected_data
        X = sr.scratchReader.X
        Y = sr.scratchReader.Y
        sr.correcte_data_plot.plot_surface(X, Y, Z)
