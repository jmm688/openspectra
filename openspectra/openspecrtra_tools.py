#  Developed by Joseph M. Conti and Joseph W. Boardman on 1/21/19 6:29 PM.
#  Last modified 1/21/19 6:29 PM
#  Copyright (c) 2019. All rights reserved.
import time
from typing import Union, List, Tuple

import numpy as np
from numpy import ma

from openspectra.image import Image, GreyscaleImage, RGBImage, Band
from openspectra.openspectra_file import OpenSpectraFile, OpenSpectraHeader
from openspectra.utils import OpenSpectraDataTypes, OpenSpectraProperties, Logger, LogHelper


class RegionOfInterest:

    def __init__(self, area:np.ndarray, x_zoom_factor:float, y_zoom_factor:float,
            image_height:int, image_width:int, image_name:str, display_name=None,
            map_info:OpenSpectraHeader.MapInfo=None):
        """area is basically a list of [x, y] pairs, that is the area should have a shape
        of (num pixels, 2)"""

        shape = area.shape
        if len(shape) != 2:
            raise ValueError("Parameter 'area' dimensions are not valid, expect a 2 dimensional array")

        if shape[1] != 2:
            raise ValueError(
                "Parameter 'area' dimensions are not valid, expect the second dimension of the array to be 2")

        # index to use when we're being iterated over
        self.__index = -1

        # generate an id that will be unique for the life of the object only
        # TODO replace with __dict__
        self.__id = str(self)
        self.__display_name = display_name

        # TODO do I need to keep these around?
        # self.__x_scale = x_zoom_factor
        # self.__y_scale = y_zoom_factor

        # TODO do I need to keep area?
        # self.__area = area

        # TODO need a way we can tie this region back to the original image?
        # TODO verify area is less than or equal to image size???
        self.__image_height = image_height
        self.__image_width = image_width
        self.__image_name = image_name

        # TODO would need this to get me back to the original image
        self.__band_name = None

        # split the points back into x and y values and convert to 1 to 1 space and 0 based
        self.__x_points = np.floor(area[:, 0] / x_zoom_factor).astype(np.int16)
        self.__y_points = np.floor(area[:, 1] / y_zoom_factor).astype(np.int16)

        if self.__x_points.size != self.__y_points.size:
            raise ValueError("Number of x points doesn't match number of y points")

        # limit to use when we're being iterated over
        self.__iter_limit = self.__x_points.size - 1

        # TODO need to implement rotation calc
        self.__x_coords = None
        self.__y_coords = None
        self.__map_info:OpenSpectraHeader.MapInfo = map_info
        self.__calculate_coords()

    def __iter__(self):
        # make sure index is at -1
        self.__index = -1
        return self

    def __next__(self):
        if self.__index >= self.__iter_limit:
            raise StopIteration
        else:
            self.__index += 1
            return self

    def __calculate_coords(self):
        if self.__map_info is not None:
            self.__x_coords = (self.__x_points - (self.__map_info.x_reference_pixel() - 1)) * self.__map_info.x_pixel_size() + self.__map_info.x_zero_coordinate()
            self.__y_coords = self.__map_info.y_zero_coordinate() - (self.__y_points - (self.__map_info.y_reference_pixel() - 1)) * self.__map_info.y_pixel_size()

    # TODO get rid of this implement __dict__?
    def id(self) -> str:
        return self.__id

    # TODO remove?
    # def area(self) -> np.ndarray:
    #     return self.__area

    def x_point(self) -> int:
        """get the x point while iterating"""
        return self.__x_points[self.__index]

    def y_point(self) -> int:
        """get the y point while iterating"""
        return self.__y_points[self.__index]

    def x_coordinate(self) -> float:
        """get the x coordinate while iterating"""
        if self.__x_coords is not None:
            return self.__x_coords[self.__index]
        else:
            return None

    def y_coordinate(self) -> float:
        """get the y coordinate while iterating"""
        if self.__y_coords is not None:
            return self.__y_coords[self.__index]
        else:
            return None

    def x_points(self) -> np.ndarray:
        return self.__x_points

    def y_points(self) -> np.ndarray:
        return self.__y_points

    def image_height(self) -> int:
        return self.__image_height

    def image_width(self) -> int:
        return self.__image_width

    def image_name(self) -> str:
        return self.__image_name

    def display_name(self) -> str:
        return self.__display_name

    def set_display_name(self, name:str):
        self.__display_name = name

    def map_info(self) -> OpenSpectraHeader.MapInfo:
        return self.__map_info

    def set_map_info(self, map_info:OpenSpectraHeader.MapInfo):
        self.__map_info = map_info
        self.__calculate_coords()


class PlotData:

    def __init__(self, x_data:np.ndarray, y_data:np.ndarray,
            x_label:str=None, y_label:str=None, title:str=None, color:str= "b",
            line_style:str= "-", legend:str=None):
        self.x_data = x_data
        self.y_data = y_data
        self.x_label = x_label
        self.y_label = y_label
        self.title = title
        self.color = color
        self.line_style = line_style
        self.legend = legend


class LinePlotData(PlotData):

    def __init__(self, x_data:np.ndarray, y_data:np.ndarray,
            x_label:str=None, y_label:str=None, title:str=None, color:str= "b",
            line_style:str= "-", legend:str=None):
        super().__init__(x_data, y_data, x_label, y_label, title, color, line_style, legend)


class HistogramPlotData(PlotData):

    def __init__(self, x_data:np.ndarray, y_data:np.ndarray, bins:int,
            x_label:str=None, y_label:str=None, title:str=None, color:str= "b",
            line_style:str= "-", legend:str=None,
            lower_limit:Union[int, float]=None, upper_limit:Union[int, float]=None):
        super().__init__(x_data, y_data, x_label, y_label, title, color, line_style, legend)
        self.bins = bins
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit


class Bands:

    def __init__(self, bands:np.ndarray, labels:List[Tuple[str, str]]):
        self.__bands = bands
        self.__labels = labels

        # TODO verify indexing matching up

    def bands(self)-> np.ndarray:
        return self.__bands

    def labels(self) -> List[Tuple[str, str]]:
        return self.__labels


class BandStatistics(Bands):

    def __init__(self, bands:np.ndarray):
        super().__init__(bands)
        self.__mean = bands.mean(0)
        # TODO is this correct?
        self.__min = bands.min(0)
        # TODO is this correct?
        self.__max = bands.max(0)
        self.__std = bands.std(0)
        self.__mean_plus = self.__mean + self.__std
        self.__mean_minus = self.__mean - self.__std

    def mean(self) -> np.ndarray:
        return self.__mean

    def min(self) -> np.ndarray:
        return self.__min

    def max(self) -> np.ndarray:
        return self.__max

    def plus_one_std(self)-> np.ndarray:
        return self.__mean_plus

    def minus_one_std(self)-> np.ndarray:
        return self.__mean_minus

    def std(self):
        return self.__std


class BandStaticsPlotData():

    def __init__(self, __band_stats:BandStatistics, wavelengths:np.ndarray, title:str=None):
        self.__band_stats = __band_stats
        self.__wavelengths = wavelengths
        if title is not None:
            self.__title = title
        else:
            self.__title = "Band Stats"

    def mean(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.mean(),
            "Wavelength", "Brightness", self.__title, "b", legend="mean")

    def min(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.min(),
            "Wavelength", "Brightness", self.__title, "r", legend="min")

    def max(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.max(),
            "Wavelength", "Brightness", self.__title, "r", legend="max")

    def plus_one_std(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.plus_one_std(),
            "Wavelength", "Brightness", self.__title, "g", legend="std+")

    def minus_one_std(self) -> LinePlotData:
        return LinePlotData(self.__wavelengths, self.__band_stats.minus_one_std(),
            "Wavelength", "Brightness", self.__title, "g", legend="std-")


class OpenSpectraBandTools:
    """A class for working on OpenSpectra files"""

    __LOG:Logger = LogHelper.logger("OpenSpectraBandTools")

    def __init__(self, file:OpenSpectraFile):
        self.__file = file

    def __del__(self):
        self.__file = None

    def bands(self, lines:Union[int, tuple, np.ndarray], samples:Union[int, tuple, np.ndarray]) -> Bands:
        # return Bands(OpenSpectraBandTools.__bogus_noise_cleanup(self.__file.bands(lines, samples)))
        # TODO cleaned or not?
        return Bands(self.__file.bands(lines, samples))

    def band_statistics(self, lines:Union[int, tuple, np.ndarray], samples:Union[int, tuple, np.ndarray]) -> BandStatistics:
        return BandStatistics(OpenSpectraBandTools.__bogus_noise_cleanup(self.__file.bands(lines, samples)))

    def statistics_plot(self, lines:Union[int, tuple, np.ndarray], samples:Union[int, tuple, np.ndarray],
            title:str=None) -> BandStaticsPlotData:
        band_stats = self.band_statistics(lines, samples)
        return BandStaticsPlotData(band_stats, self.__file.header().wavelengths(), title)

    def spectral_plot(self, line:int, sample:int) -> LinePlotData:
        band = OpenSpectraBandTools.__bogus_noise_cleanup(self.__file.bands(line, sample))

        wavelengths = self.__file.header().wavelengths()
        # OpenSpectraBandTools.__LOG.debug("plotting spectra with min: {0}, max: {1}", band.min(), band.max())
        return LinePlotData(wavelengths, band, "Wavelength", "Brightness",
            "Spectra S-{0}, L-{1}".format(sample + 1, line + 1))

    # TODO work around for now for 1 float file, remove noise from data for floats
    # TODO will need a general solution also for images too?
    # TODO where will this live
    @staticmethod
    def __bogus_noise_cleanup(bands:np.ndarray) -> np.ndarray:
        clean_bands = bands
        if clean_bands.dtype in OpenSpectraDataTypes.Floats:
            if clean_bands.min() == np.nan or clean_bands.max() == np.nan or clean_bands.min() == np.inf or clean_bands.max() == np.inf:
                clean_bands = ma.masked_invalid(clean_bands)

            # TODO certain areas look a bit better when filtered by different criteria, must be a better way
            # if clean_bands.std() > 1.0:
            # if clean_bands.std() > 0.1:
            # clean_bands = ma.masked_outside(clean_bands, -0.01, 0.05)
            clean_bands = ma.masked_outside(clean_bands, 0.0, 1.0)

        return clean_bands


class OpenSpectraRegionTools:
    """A class for working with Regions of Interest"""

    __LOG:Logger = LogHelper.logger("OpenSpectraRegionTools")

    def __init__(self, region:RegionOfInterest, band_tools:OpenSpectraBandTools):
        self.__region = region
        self.__band_tools = band_tools
        self.__map_info:OpenSpectraHeader.MapInfo = self.__region.map_info()

        self.__projection = self.__map_info.projection_name()
        if self.__map_info.projection_zone() is not None:
            self.__projection += (" " + str(self.__map_info.projection_zone()))
        if self.__map_info.projection_area() is not None:
            self.__projection += (" " + self.__map_info.projection_area())
        self.__projection += (" " + self.__map_info.datum())

        if self.__map_info is not None:
            self.__output_format = "{0},{1},{2},{3}"
            self.__data_header = "sample,line,x_coordinate,y_coordinate"
        else:
            self.__output_format = "{0},{1}"
            self.__data_header = "sample,line"

    def save_region(self, file_name:str, include_bands:bool=False):
        OpenSpectraRegionTools.__LOG.debug("Save region to: {0}", file_name)
        # OpenSpectraRegionTools.__LOG.debug("Area: {0}", self.__region.area().tolist())

        with open(file_name, "w") as out:
            out.write("name:{0}\n".format(self.__region.display_name()))
            out.write("description:{0}\n".format(self.__region.image_name()))
            out.write("image width:{0}\n".format(self.__region.image_width()))
            out.write("image height:{0}\n".format(self.__region.image_height()))
            out.write("projection:{0}\n".format(self.__projection))
            out.write("data:\n")
            # TODO add band names to header optionally
            # TODO x_coordinate & y_coordinate only if we have map info

            out.write(self.__get_data_header(include_bands))

            output_format = self.__get_output_format(include_bands)
            for r in self.__region:
                out.write(output_format.format(r.x_point() + 1, r.y_point() + 1, r.x_coordinate(), r.y_coordinate()))

    def __get_data_header(self, include_bands:bool) -> str:
        header:str = self.__data_header
        if include_bands:
            pass

        return header + "\n"

    def __get_output_format(self, include_bands:bool) -> str:
        output_format = self.__output_format
        if include_bands:
            pass

        return output_format + "\n"


class OpenSpectraImageTools:
    """A class for creating Images from OpenSpectra files"""

    def __init__(self, file:OpenSpectraFile):
        self.__file = file

    def __del__(self):
        self.__file = None

    def greyscale_image(self, band:int, label:str=None) -> GreyscaleImage:
        return GreyscaleImage(self.__file.raw_image(band), label)

    def rgb_image(self, red:int, green:int, blue:int,
            red_label:str=None, green_label:str=None, blue_label:str=None) -> RGBImage:
        # Access each band seperately so we get views of the data for efficiency
        return RGBImage(self.__file.raw_image(red), self.__file.raw_image(green),
            self.__file.raw_image(blue), red_label, green_label, blue_label)


class OpenSpectraHistogramTools:
    """A class for generating histogram data from Images"""

    def __init__(self, image:Image):
        self.__image = image
        if isinstance(self.__image, GreyscaleImage):
            self.__type = "greyscale"
        elif isinstance(self.__image, RGBImage):
            self.__type = "rgb"
        else:
            raise TypeError("Unknown image type")

    def __del__(self):
        self.__image = None

    def raw_histogram(self, band:Band=None) -> HistogramPlotData:
        """If band is included and the image is Greyscale it is ignores
        If image is RGB and band is missing an error is raised"""

        if self.__type == "rgb" and band is None:
            raise ValueError("band argument is required when image is RGB")

        raw_data = self.__image.raw_data(band)
        plot_data = OpenSpectraHistogramTools.__get_hist_data(raw_data)
        plot_data.x_label = "X-FixMe"
        plot_data.y_label = "Y-FixMe"
        plot_data.title = "Raw " + self.__image.label(band)
        plot_data.color = "r"
        plot_data.lower_limit = self.__image.low_cutoff(band)
        plot_data.upper_limit = self.__image.high_cutoff(band)
        return plot_data

    def adjusted_histogram(self, band:Band=None) -> HistogramPlotData:

        if self.__type == "rgb" and band is None:
            raise ValueError("band argument is required when image is RGB")

        image_data = self.__image.image_data(band)
        plot_data = OpenSpectraHistogramTools.__get_hist_data(image_data)
        plot_data.x_label = "X-FixMe"
        plot_data.y_label = "Y-FixMe"
        plot_data.title = "Adjusted " + self.__image.label(band)
        plot_data.color = "b"
        return plot_data

    @staticmethod
    def __get_hist_data(data:np.ndarray) -> HistogramPlotData:
        type = data.dtype
        if type in OpenSpectraDataTypes.Ints:
            x_range = (data.min(), data.max())
            bins = data.max() - data.min()
            return HistogramPlotData(x_range, data.flatten(), bins=bins)
        elif type in OpenSpectraDataTypes.Floats:
            x_range = (data.min(), data.max())
            bins = OpenSpectraProperties.FloatBins
            return HistogramPlotData(x_range, data.flatten(), bins=bins)
        else:
            raise TypeError("Data with type {0} is not supported".format(type))
