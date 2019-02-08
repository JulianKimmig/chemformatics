import logging
import os

import numpy as np
import pandas as pd
from numpy.core.multiarray import ndarray
from scipy import interpolate

from jsonconfig import JsonConfig

default_x_dist = 20

raw_data_path = ["data", "raw", "path"]


# noinspection PyBroadException
class ScratchReader:
    raw_data: ndarray
    available_separators = ["\t", ",", " ", ";"]
    available_raw_structs = ["YZYZ", "Z-Matrix"]
    available_interpolation_methods = ["linear", "nearest"]

    def __init__(self, options=None):
        self.options = JsonConfig(data=options)
        self.interpolated_file = None
        self.raw_file = None

        self.correction_surface = np.array([[]])  # corrected Zs (with nan)
        self.raw_data = np.array([()])  # raw triples[(x1,y1,z1),...]
        self.X = np.array([[]])  # Y grid
        self.Y = np.array([[]])  # X grid
        self.Z = np.array([[]])  # interpolated data
        self.corrected_data = np.array([[]])
        self.correction_points = self.correction_points

    def read_interpolated(self, interpolated_file=None):
        logging.info("open interpol")
        if interpolated_file is not None:
            self.interpolated_file = interpolated_file
        if self.interpolated_file is not None:
            if os.path.exists(self.interpolated_file):
                interpolated = pd.read_csv(
                    self.interpolated_file, header=0, index_col=0
                )
                x = np.array(interpolated.columns).astype(float)
                y = np.array(interpolated.index).astype(float)
                self.Z = interpolated.values
                self.X = (
                    np.repeat(x, self.Z.shape[0])
                    .reshape(self.Z.shape[1], self.Z.shape[0])
                    .transpose()
                )
                self.Y = np.repeat(y, self.Z.shape[1]).reshape(self.Z.shape)
            else:
                self.interpolated_file = None

    def save_interpolated(self, interpolated_file=None):
        if interpolated_file is not None:
            self.interpolated_file = interpolated_file
        if self.interpolated_file is not None:
            df = pd.DataFrame(self.Z)
            df.columns = self.x.astype(str)
            df.index = self.y.astype(str)
            df.to_csv(self.interpolated_file)

    def read_raw(self, raw_file=None, structure=None, encoding=None, sep=None):
        logging.info("read raw")
        if raw_file is not None:
            self.raw_file = raw_file

        if structure is None:
            structure = self.raw_data_structure

        if encoding is None:
            encoding = self.raw_data_encoding

        if sep is None:
            sep = self.raw_data_separator

        if self.raw_file is None:
            return pd.DataFrame()

        df = pd.read_csv(self.raw_file, encoding=encoding, sep=sep)

        try:
            if structure == "YZYZ":
                self._read_raw_yzyz(df)
            if structure == "Z-Matrix":
                self._read_raw_z_matrix(df)
            else:
                self._read_raw_yzyz(df)
        except Exception as e:
            logging.exception(e)
            return

        return df

    def _read_raw_z_matrix(self, df):
        df = df.dropna(1)
        df = df.dropna()


        self.Z = df.values*self.options.get("measurement", "z_fac", default=1)
        self.x = np.arange(0, df.values.shape[1], 1)*self.options.get("measurement", "x_fac", default=1)
        self.y = np.arange(0, df.values.shape[0], 1)*self.options.get("measurement", "y_fac", default=1)
        df.columns = self.x.astype(str)
        df.index = self.y.astype(str)
        self.raw_data = np.array(
            [np.tile(self.x, len(self.y)), np.repeat(self.y, len(self.x)), self.Z.flatten()]
        ).T

        return self.raw_data

    def _read_raw_yzyz(self, df):
        df = df.dropna(1)
        data = df.values

        newdata = []
        miny = +np.inf
        maxy = -np.inf
        for i in range(0, data.shape[1] - 1, 2):
            x = i / 2
            z = data[:, [1 + i]].reshape(1, -1)[0]
            y = data[:, [0 + i]].reshape(1, -1)[0]
            miny = min(miny, y.min())
            maxy = max(maxy, y.max())

            for j in range(len(z)):
                newdata.append((x, y[j], z[j]))

        self.raw_data = np.array(newdata) * np.array(
            [
                self.options.get("measurement", "x_fac", default=1),
                self.options.get("measurement", "y_fac", default=1),
                self.options.get("measurement", "z_fac", default=1),
            ]
        )

        return self.raw_data

    def add_correction_point(self, x, y, z):

        na = self.correction_points
        for i in reversed(range(len(na))):
            if na[i][0] == x and na[i][1] == y:
                logging.info("replaceCP " + str(x) + " "+ str(y) + " "+ str(z))
                na[i] = [x, y, z]
                self.correction_points = na
                return
        logging.info("addCP " + str(x) + " "+ str(y) + " "+ str(z))
        self.correction_points = self.correction_points + [
            [float(x), float(y), float(z)]
        ]

    def remove_correction_point(self, x, y):
        logging.info("removeCP", x, y)
        na = self.correction_points
        for i in reversed(range(len(na))):
            if na[i][0] == x and na[i][1] == y:
                na.pop(i)
        self.correction_points = na

    def interpolate(self, method=None, resolution=None):
        if self.raw_data.size < 2:
            return
        logging.info("interpolate")
        if len(self.raw_data.shape) < 2:
            return
        if method is None:
            method = self.interpolation_method
        if resolution is None:
            resolution = self.interpolation_resolution
        try:
            resolution = float(resolution)
            resolution = [resolution, resolution]
        except:
            pass
        max_values = np.amax(self.raw_data, axis=0)
        min_values = np.amin(self.raw_data, axis=0)
        xy_size = max_values - min_values
        t_x, t_y = np.meshgrid(
            np.linspace(
                min_values[0], max_values[0], max(3, int(xy_size[0] / resolution[0]))
            ),
            np.linspace(
                min_values[1], max_values[1], max(3, int(xy_size[1] / resolution[1]))
            ),
        )
        t_z = interpolate.griddata(
            self.raw_data[:, :2], self.raw_data[:, 2], (t_x, t_y), method=method
        )
        mask = np.all(np.isnan(t_z), axis=1)
        t_x = t_x[~mask]
        t_y = t_y[~mask]
        t_z = t_z[~mask]
        mask = np.all(np.isnan(t_z), axis=0)

        self.X = t_x.transpose()[~mask].transpose()
        self.Y = t_y.transpose()[~mask].transpose()
        self.Z = t_z.transpose()[~mask].transpose()

        self.calculate_correction_surface()
        return t_x, t_y, t_z

    def calculate_correction_surface(self, cut_lower=0, cut_upper=0):
        logging.info("calc corr surf")
        p = np.array(self.correction_points)

        if len(p) > 3:
            self.correction_surface = interpolate.griddata(
                p[:, :2], p[:, 2], (self.X, self.Y), method="cubic"
            )
            self.corrected_data = self.Z - self.correction_surface
            if cut_upper > 0 and np.nanmax(self.corrected_data) > 0:
                maxval = np.nanmax(self.corrected_data) * cut_upper
                self.corrected_data[
                    (self.corrected_data < maxval) * (self.corrected_data > 0)
                ] = 0
            if cut_lower > 0 > np.nanmin(self.corrected_data):
                minval = np.nanmin(self.corrected_data) * cut_lower
                self.corrected_data[
                    (self.corrected_data > minval) * (self.corrected_data < 0)
                ] = 0
                self.options.put(
                    *["data", "correction", "cut", "lower"], value=cut_lower
                )
                self.options.put(
                    *["data", "correction", "cut", "upper"], value=cut_upper
                )
            self.corrected_data[self.corrected_data == 0] = np.nan

    def open(self, file, read=True):
        logging.info("open file "+file)
        self.options.read(file)
        if self.raw_file is not None and read:
            self.read_raw()
        if self.interpolated_file is not None and read:
            self.read_interpolated()

    def get_raw_file(self):
        return self.options.get(*raw_data_path, default=None)

    def set_raw_file(self, file):
        self.options.put(*raw_data_path, value=file)

    raw_file = property(get_raw_file, set_raw_file)

    def get_raw_structure(self):
        return self.options.get(
            *["data", "raw", "struc"], default=self.available_separators[0]
        )

    def set_raw_structure(self, structure):
        self.options.put(*["data", "raw", "struc"], value=structure)

    raw_data_structure = property(get_raw_structure, set_raw_structure)

    def get_raw_encoding(self):
        return self.options.get(*["data", "raw", "encoding"], default="ansi")

    def set_raw_encoding(self, encoding):
        self.options.put(*["data", "raw", "encoding"], value=encoding)

    raw_data_encoding = property(get_raw_encoding, set_raw_encoding)

    def get_raw_separator(self):
        return self.options.get(
            *["data", "raw", "separator"], default=self.available_separators[0]
        )

    def set_raw_separator(self, separator):
        self.options.put(*["data", "raw", "separator"], value=separator)

    raw_data_separator = property(get_raw_separator, set_raw_separator)

    def get_interpolated_file(self):
        return self.options.get(*["data", "interpolated", "path"], default=None)

    def set_interpolated_file(self, file):
        self.options.put(*["data", "interpolated", "path"], value=file)

    interpolated_file = property(get_interpolated_file, set_interpolated_file)

    def get_interpolation_method(self):
        return self.options.get(
            *["data", "interpolated", "method"],
            default=self.available_interpolation_methods[0]
        )

    def set_interpolation_method(self, method):
        self.options.put(*["data", "interpolated", "method"], value=method)

    interpolation_method = property(get_interpolation_method, set_interpolation_method)

    def get_interpolation_resolution(self):
        return self.options.get(*["data", "interpolated", "resolution"], default=[1, 1])

    def set_interpolation_resolution(self, resolution):
        self.options.put(*["data", "interpolated", "resolution"], value=resolution)

    interpolation_resolution = property(
        get_interpolation_resolution, set_interpolation_resolution
    )

    def get_correction_points(self):
        return self.options.get(*["data", "correction", "points"], default=[])

    def set_correction_points(self, points):
        self.options.put(*["data", "correction", "points"], value=points)

    correction_points = property(get_correction_points, set_correction_points)

    def get_x(self):
        return self.X[0, :]

    def set_x(self, x):
        assert len(x) == self.Z.shape[1]
        self.X = np.tile(x, self.Z.shape[0]).reshape(self.Z.shape)

    x = property(get_x, set_x)

    def get_y(self):
        return self.Y[:, 0]

    def set_y(self, y):
        assert len(y) == self.Z.shape[0]
        self.Y = np.repeat(y, self.Z.shape[1]).reshape(self.Z.shape)

    y = property(get_y, set_y)

    def get_z(self, x, y):
        x_dist = self.x - x
        y_dist = self.y - y
        outerp = np.outer(x_dist, y_dist)
        amin = np.argmin(outerp * outerp)
        yi = amin % outerp.shape[1]
        xi = int((amin - y) / outerp.shape[1])

        return self.Z[yi][xi]
