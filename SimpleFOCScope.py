# This Python file uses the following encoding: utf-8
from PySide6.QtGui import QPolygonF
from PySide6.QtQml import QQmlProperty, QmlElement
from PySide6.QtQuick import QQuickItem
from PySide6.QtCore import Signal, Property, Slot, QGenericArgument
import PySide6.QtCharts #critical for QObject returned from self._chart.createSeriesWithLabel() to be casted in QLineSeries
import shiboken6
import ctypes
import numpy as np
import Product

class SimpleFOCScope(Product.Product):
    def __init__(self, parent = None):
        super(SimpleFOCScope, self).__init__(parent)
        self._xdata = None
        self._spacing = 500.0
        self._normalize = False
        self._chart = None
        self.arrays = {}
        self.buffers = {}
        self._xMin = 0
        self._xMax = 0
        self._yMin = 0
        self._yMax = 0
        self._dtypes = {}
        self._selected = {}


    def _update(self):
        self._xdata = None
        for dataSource in self.dataSources:

            new = np.hstack(self.arrays[dataSource])
            
            if dataSource in self.buffers:
                self.buffers[dataSource] = np.hstack([self.buffers[dataSource], new])
            else:
                self.buffers[dataSource] = new

            self.arrays[dataSource] = []
    
    dataSourcesChanged = Signal()
    @Property(list, notify = dataSourcesChanged)
    def dataSources(self):
        return list(self.arrays.keys())
    
    Product.InputProperty(vars(), QQuickItem, "chart")


    Product.ROProperty(vars(), float, "xMax")
    Product.ROProperty(vars(), float, "xMin")
    Product.ROProperty(vars(), float, "yMax")
    Product.ROProperty(vars(), float, "yMin")

    @Slot(str, object)
    def dataReceived(self, name, buffer):
        if name not in self.arrays:
            self.arrays[name] = []
            self.dataSourcesChanged.emit()

        self.arrays[name].append(buffer)
        self.makeDirty()

    @Slot(str)
    def toggleDatasource(self, channel):
        
        if channel in self._selected:
            label_to_series_map = self._selected[channel] 
            for (label, serie) in label_to_series_map.items():
                self._chart.removeSeries(serie) #QMLWrapper "hack"
            
            del self._selected[channel]
        else:
            self._selected[channel] = None #will be added in refresh()

    @Slot()
    def refresh(self):
        '''
            index: the series index
            channel: the channel index (relative to roi start)
        '''
        def series_to_polyline(xdata, ydata):
            #inspired from https://github.com/PierreRaybaut/plotpy/wiki/Using-Qt-Charts-(PyQtChart)-to-plot-curves-efficiently-in-Python!
            size = len(xdata)
            polyline = QPolygonF()
            polyline.resize(size)
            address = shiboken6.getCppPointer(polyline.data())[0]
            buffer = (2 * size * ctypes.c_double).from_address(address) #QPolygonF float type is qreal, which is double
            memory = np.frombuffer(buffer, xdata.dtype)
            memory[:(size-1)*2+1:2] = xdata
            memory[1:(size-1)*2+2:2] = ydata
            return polyline

        self.update()

        y_min = np.finfo(np.float32).max
        y_max = np.finfo(np.float32).min
        x_min = np.finfo(np.float32).max
        x_max = np.finfo(np.float32).min
        for (dataSource, label_to_series_map) in self._selected.items():

            data = self.buffers[dataSource]
            if data is None:
                break
            
            if label_to_series_map is None:
                label_to_series_map = self._selected[dataSource] = {label:None for label in data.dtype.fields.keys()}
            for (label, serie) in label_to_series_map.items():
                channel_data = data[label]
                if channel_data.size == 0:
                    break

                min_shape = np.fmin(channel_data.shape[0], 100)
                if self._xdata is None:
                    self._xdata = np.linspace(np.fmax(0, channel_data.shape[0]-100), channel_data.shape[0], np.fmin(channel_data.shape[0], 100), np.float32)

                if self._normalize:
                    channel_data -= np.mean(channel_data)

                polygon = series_to_polyline(self._xdata, channel_data[-min_shape:])
                
                x_min = np.fmin(x_min, self._xdata.min())
                x_max = np.fmax(x_max, self._xdata.max())
                y_min = np.fmin(y_min, channel_data.min())
                y_max = np.fmax(y_max, channel_data.max())


                if serie is None:
                    serie = label_to_series_map[label] = self._chart.createSeriesWithLabel(f"{dataSource}_{label}") # workaround: calling self.chart_.createSeries(...) returns None instead of a QLineSeries instance

                if serie.count() > 0:
                    serie.replace(polygon)
                else:
                    serie.append(polygon)

        self.set_xMin(self, x_min)
        self.set_xMax(self, x_max)
        self.set_yMin(self, y_min)
        self.set_yMax(self, y_max)