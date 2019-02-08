import logging

import matplotlib as mpl
import numpy as np
import pandas as pd
import scipy
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from qtpy import QtCore

class LegendCanvas(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure()
        self.axis = self.fig.add_axes([0, 0.5, 1, 0.3])

        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Minimum)
        FigureCanvas.updateGeometry(self)

    #     self.surface = None
    #     self.colorbar = None
    #      self.points = []
    #       self.surface_type = "mesh"
    #        self.plot()

    def plot_cmap(self, cmap, min, max):
        norm = mpl.colors.Normalize(vmin=min, vmax=max)
        # ax, _ = mpl.colorbar.make_axes(self.axis,norm=norm,cmap=cmap, orientation="horizontal")
        cb1 = mpl.colorbar.ColorbarBase(
            self.axis, cmap=cmap, norm=norm, orientation="horizontal"
        )

class Point:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z


class FigureCanvas2D(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(
            # figsize=(width, height), dpi=dpi
        )
        self.surface_axis = self.fig.add_subplot(111)
        self.surface_axis.autoscale(enable=True, axis="x", tight=True)
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.surface = None
        self.colorbar = None
        self.points = []
        self.surface_type = "mesh"
        self.plot()

    def removePoint(self, p, replot=True):
        if p in self.points:
            self.points.remove(p)
            if replot:
                self.plot()
        return p

    def addPoint(self, x, y, z, replot=True):
        p = Point(x, y, z)
        self.points.append(p)
        if replot:
            self.plot()
        return p

    def set_surfaceType(self, type):
        if type != self.surface_type:
            self.surface_type = type
            self.plot()
        return self.surface_type

    def plot_surface(self, X, Y, Z):
        logging.info("plot surface")
        maxpoints = 100000
        if Z.size > maxpoints:
            newX=int(np.math.sqrt(maxpoints * Z.shape[1] / Z.shape[0]))
            newY=int(maxpoints/newX)
            Z = rebin(Z,(newY, newX))
            X = rebin(X,(newY, newX))
            Y = rebin(Y,(newY, newX))

        if Z.size > 0:
            self.resolution = np.array(
                [np.amin(np.diff(X, axis=1)), np.amin(np.diff(Y, axis=0))]
            )
            self.surface = (X, Y, Z)
            self.plot()

    def plot(self):
        self.surface_axis.clear()
        mesh = None
        if self.surface is not None:
            if self.surface_type == "contour":
                mesh = self.surface_axis.contourf(
                    self.surface[0] + self.resolution[0] / 2,
                    self.surface[1] + self.resolution[1] / 2,
                    self.surface[2],
                    levels=100
                    #                   cmap=cmap,norm=MidpointNormalize(midpoint=np.nanmean(Z),vmin=np.nanmin(Z), vmax=np.nanmax(Z))
                )
            elif self.surface_type == "mesh":
                mesh = self.surface_axis.pcolormesh(
                    self.surface[0],
                    self.surface[1],
                    self.surface[2],
                    #                   cmap=cmap,norm=MidpointNormalize(midpoint=np.nanmean(Z),vmin=np.nanmin(Z), vmax=np.nanmax(Z))
                )
        for p in self.points:
            self.surface_axis.plot(p.x, p.y, marker="o", markersize=5, color="red")
        if mesh is not None:
            if self.colorbar is None:
                self.colorbar = self.fig.colorbar(mappable=mesh, ax=self.surface_axis)

        self.surface_axis.figure.canvas.draw()

def rebin(a, newshape):
    """Rebin an array to a new shape.
    """
    assert len(a.shape) == len(newshape)

    slices = [slice(0, old, float(old) / new) for old, new in zip(a.shape, newshape)]
    coordinates = scipy.mgrid[slices]
    indices = coordinates.astype("i")  # choose the biggest smaller integer index
    return a[tuple(indices)]


class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df=None, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=parent)
        if df is None:
            df = pd.DataFrame()
        self._df = df

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if orientation == QtCore.Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError,):
                return QtCore.QVariant()
        elif orientation == QtCore.Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return self._df.index.tolist()[section]
            except (IndexError,):
                return QtCore.QVariant()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()

        if not index.isValid():
            return QtCore.QVariant()

        return QtCore.QVariant(str(self._df.ix[index.row(), index.column()]))

    def setData(self, index, value, role):
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        if hasattr(value, "toPyObject"):
            # PyQt4 gets a QVariant
            value = value.toPyObject()
        else:
            # PySide gets an unicode
            dtype = self._df[col].dtype
            if dtype != object:
                value = None if value == "" else dtype.type(value)
        self._df.set_value(row, col, value)
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(
            colname, ascending=order == QtCore.Qt.AscendingOrder, inplace=True
        )
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()


def saveFileNameDialog(title="open file", location=None, types="All Files (*);"):
    if location is None:
        location = ""
    options = QFileDialog.Options()
    # options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getSaveFileName(
        None, title, location, types, options=options
    )
    return fileName


def openFileNameDialog(title="open file", location=None, types="All Files (*);"):
    if location is None:
        location = ""
    options = QFileDialog.Options()
    # options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(
        None, title, location, types, options=options
    )
    return fileName

