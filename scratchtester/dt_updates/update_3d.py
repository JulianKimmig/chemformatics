import logging
import math
import numpy
import pyqtgraph.opengl as gl
from matplotlib import pyplot
from pyqtgraph import Vector, Transform3D
from qtpy import QtWidgets

from dt_updates.sidefunctions import LegendCanvas, rebin

fire = True


def updateview_object(sr):
    global fire
    if fire:
        xscale = sr.ui.scale_3d_x.value()
        yscale = sr.ui.scale_3d_y.value()
        zscale = sr.ui.scale_3d_z.value()

        sr.scratchReader.options.put("view", "3d", "scale", "x", value=xscale)
        sr.scratchReader.options.put("view", "3d", "scale", "y", value=yscale)
        sr.scratchReader.options.put("view", "3d", "scale", "z", value=zscale)

        for i in sr.ui.plot3d_pot_widget.items:
            t = i.viewTransform().copyDataTo()
            t[0] = xscale
            t[5] = yscale
            t[10] = zscale
            i.setTransform(Transform3D(t))
            # i.scale(xscale, yscale, zscale, local=True)


def updateview_camera(sr):
    global fire
    if fire:
        x = sr.ui.slider_3d_camera_x.value()
        y = sr.ui.slider_3d_camera_y.value()
        z = sr.ui.slider_3d_camera_z.value()
        distance = sr.ui.slider_3d_distance.value()
        azimute = sr.ui.slider_3d_azimute.value()
        elevation = sr.ui.slider_3d_elevation.value()

        sr.scratchReader.options.put(
            "view", "3d", "camera", "position", value=[x, y, z]
        )
        sr.scratchReader.options.put("view", "3d", "camera", "azimute", value=azimute)
        sr.scratchReader.options.put("view", "3d", "camera", "distance", value=distance)
        sr.scratchReader.options.put(
            "view", "3d", "camera", "elevation", value=elevation
        )
        sr.ui.plot3d_pot_widget.opts["center"] = Vector(x, y, z)
        sr.ui.plot3d_pot_widget.setCameraPosition(
            distance=distance, elevation=elevation, azimuth=azimute
        )


def generate_ui_3d(sr):
    logging.info("generate 3D")
    # pg.setConfigOption('background', 'w')
    # pg.setConfigOption('foreground', 'k')

    view = gl.GLViewWidget()
    view.setMinimumSize(sr.ui.plot3d_pot_widget.minimumSize())
    view.setObjectName(sr.ui.plot3d_pot_widget.objectName())
    sr.ui.plot3d_pot_widget.parent().layout().replaceWidget(
        sr.ui.plot3d_pot_widget, view
    )
    sr.ui.plot3d_pot_widget = view

    sr.ui.slider_3d_camera_z.sliderMoved.connect(lambda: updateview_camera(sr))
    sr.ui.slider_3d_camera_y.sliderMoved.connect(lambda: updateview_camera(sr))
    sr.ui.slider_3d_camera_x.sliderMoved.connect(lambda: updateview_camera(sr))
    sr.ui.slider_3d_elevation.sliderMoved.connect(lambda: updateview_camera(sr))
    sr.ui.slider_3d_distance.sliderMoved.connect(lambda: updateview_camera(sr))
    sr.ui.slider_3d_azimute.sliderMoved.connect(lambda: updateview_camera(sr))

    sr.ui.scale_3d_x.valueChanged.connect(lambda: updateview_object(sr))
    sr.ui.scale_3d_y.valueChanged.connect(lambda: updateview_object(sr))
    sr.ui.scale_3d_z.valueChanged.connect(lambda: updateview_object(sr))

    sizePolicy = QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
    )
    sizePolicy.setHorizontalStretch(1)
    sizePolicy.setVerticalStretch(1)
    view.setSizePolicy(sizePolicy)

    view.show()
    sr.legend3d_canvas = LegendCanvas(sr.ui.legend3d_widget)
    sr.ui.legend3d_widget.layout().addWidget(sr.legend3d_canvas)

    def plot3d_data_source_changed(m):
        d = sr.scratchReader.Z
        if m == "correction surface":
            d = sr.scratchReader.correction_surface
        elif m == "corrected":
            d = sr.scratchReader.corrected_data
        if sr.scratchReader.Z.size > 4:
            update3d(sr, sr.scratchReader.X[0, :], sr.scratchReader.Y[:, 0], d)
        updateview_camera(sr)
        updateview_object(sr)

    for item in ["interpolated", "correction surface", "corrected"]:
        sr.ui.plot3d_data_source.addItem(item)
    sr.ui.plot3d_data_source.activated[str].connect(plot3d_data_source_changed)


def update3d(sr, x, y, Z):
    if len(x) < 1 and len(y) < 1 and len(Z.shape) < 2:
        return
    logging.info("update 3d image" )
    maxpoints = 100000
    if len(x)*len(y) > maxpoints:
        newX=int(math.sqrt(maxpoints * len(x)/len(y)))
        newY=int(maxpoints/newX)
        print(newX,newY,Z.shape,len(x),len(y))
        Z = rebin(Z,(newY, newX))
        x = rebin(x.reshape(-1, 1), (newX,1)).flatten()
        y = rebin(y.reshape(-1, 1), (newY,1)).flatten()
        print(newX,newY,Z.shape,len(x),len(y))
    w = sr.ui.plot3d_pot_widget
    for i in w.items:
        w.removeItem(i)
    Z = numpy.nan_to_num(Z, 0)

    tx = (x.max() - x.min()) / 2
    ty = (y.max() - y.min()) / 2
    sr.ui.slider_3d_camera_z.setMinimum(numpy.nanmin(Z))
    sr.ui.slider_3d_camera_z.setMaximum(numpy.nanmax(Z))
    sr.ui.slider_3d_camera_x.setMinimum(-tx)
    sr.ui.slider_3d_camera_x.setMaximum(+tx)
    sr.ui.slider_3d_camera_y.setMinimum(-ty)
    sr.ui.slider_3d_camera_y.setMaximum(+ty)

    sr.ui.slider_3d_distance.setMinimum(0)
    sr.ui.slider_3d_distance.setMaximum(
        2 * max(2 * ty, 2 * tx) / (math.tan(w.opts["fov"] * math.pi / 180))
    )
    sr.ui.slider_3d_distance.setValue(
        sr.scratchReader.options.get(
            "view", "3d", "camera", "distance", default=(Z.max().item() * 10)
        )
    )
    sr.ui.slider_3d_azimute.setValue(
        sr.scratchReader.options.get("view", "3d", "camera", "azimute", default=30)
    )
    sr.ui.slider_3d_elevation.setValue(
        sr.scratchReader.options.get("view", "3d", "camera", "elevation", default=30)
    )

    cmap = pyplot.get_cmap("jet")

    minZ = Z.min()
    maxZ = Z.max()
    rgba_img = cmap((Z.T - minZ) / (maxZ - minZ))
    sr.legend3d_canvas.plot_cmap(cmap, minZ, maxZ)

    p = gl.GLSurfacePlotItem(
        x=x,
        y=y,
        z=Z.T,
        colors=rgba_img
        # shader=np.array([0.01, 40, 0.5, 0.01, 40, 1, 0.01, 40, 2])
    )
    #  p.shader()['colorMap'] =
    w.addItem(p)
    p.translate(-tx, -ty, 0)
    updateview_camera(sr)
    updateview_object(sr)


def loadfile_3d(sr):
    global fire
    fire = False
    logging.info("load 3d")

    sr.ui.scale_3d_x.setValue(
        sr.scratchReader.options.get("view", "3d", "scale", "x", default=1)
    )
    sr.ui.scale_3d_y.setValue(
        sr.scratchReader.options.get("view", "3d", "scale", "y", default=1)
    )
    sr.ui.scale_3d_z.setValue(
        sr.scratchReader.options.get("view", "3d", "scale", "z", default=1)
    )

    cx, cy, cz = sr.scratchReader.options.get(
        "view", "3d", "camera", "position", default=[0, 0, 0]
    )

    sr.ui.slider_3d_camera_z.setValue(cz)
    sr.ui.slider_3d_camera_x.setValue(cx)
    sr.ui.slider_3d_camera_y.setValue(cy)

    fire = True

    if (
        len(sr.scratchReader.X[0]) < 1
        or len(sr.scratchReader.Y[0]) < 1
        or len(sr.scratchReader.Z.shape) < 2
    ):
        logging.info("insufficient array")
        return

    update3d(sr, sr.scratchReader.X[0, :], sr.scratchReader.Y[:, 0], sr.scratchReader.Z)
