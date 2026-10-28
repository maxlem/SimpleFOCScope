# This Python file uses the following encoding: utf-8
from PySide6.QtGui import QPolygonF, QColor
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
        self._labels = []
        self._enabled = set()
        self._series = {}


    def _update(self):
        self._xdata = None
        for dataSource in list(self.arrays.keys()):
            if not self.arrays[dataSource]:
                continue

            new = np.hstack(self.arrays[dataSource])
            
            if dataSource in self.buffers:
                self.buffers[dataSource] = np.hstack([self.buffers[dataSource], new])
            else:
                self.buffers[dataSource] = new

            self.arrays[dataSource] = []
    
    dataSourcesChanged = Signal()
    @Property(list, notify = dataSourcesChanged)
    def dataSources(self):
        return list(self._labels)
    
    Product.InputProperty(vars(), QQuickItem, "chart")


    Product.ROProperty(vars(), float, "xMax")
    Product.ROProperty(vars(), float, "xMin")
    Product.ROProperty(vars(), float, "yMax")
    Product.ROProperty(vars(), float, "yMin")

    @Slot(str, object)
    def dataReceived(self, name, buffer):
        if name not in self.arrays:
            self.arrays[name] = []

        if buffer.dtype.fields:
            labels = [label for label in buffer.dtype.fields.keys() if not self._is_metadata(label)]
            if labels != self._labels:
                self._labels = labels
                self._enabled.update(labels)
                self.dataSourcesChanged.emit()

        self.arrays[name].append(buffer)
        self.makeDirty()

    @staticmethod
    def _color_for(label):
        colors = {
            'ia': '#1f77b4', 'va': '#6baed6',
            'ib': '#d62728', 'vb': '#ff9896',
            'ic': '#2ca02c', 'vc': '#98df8a',
            'vm': '#ff7f0e',
        }
        return QColor(colors.get(label, '#7f7f7f'))

    @staticmethod
    def _is_metadata(label):
        return label == 'base_timestamp_us' or label.startswith('reserved') or label.endswith('_offset_us')

    @staticmethod
    def _x_axis(data, label, count):
        offset_label = f'{label}_offset_us'
        if data.dtype.fields and 'base_timestamp_us' in data.dtype.fields and offset_label in data.dtype.fields:
            base = data['base_timestamp_us'][-count:].astype(np.float64)
            offset = data[offset_label][-count:].astype(np.float64)
            return (base + offset) * 1e-6
        return np.arange(data.shape[0] - count, data.shape[0], dtype=np.float64)

    @Slot(str, bool)
    def setChannelEnabled(self, channel, enabled):
        if enabled:
            self._enabled.add(channel)
        else:
            self._enabled.discard(channel)
            for key in list(self._series.keys()):
                if key[1] == channel:
                    serie = self._series.pop(key)
                    self._chart.removeSeries(serie)
        self.makeDirty()

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
        for (dataSource, data) in self.buffers.items():
            if data is None or data.dtype.fields is None:
                continue

            for label in data.dtype.fields.keys():
                if self._is_metadata(label) or label not in self._enabled:
                    continue

                channel_data = data[label]
                if channel_data.size == 0:
                    continue

                min_shape = int(min(channel_data.shape[0], 100))
                ydata = channel_data[-min_shape:].astype(np.float64)
                xdata = self._x_axis(data, label, min_shape)

                if self._normalize:
                    ydata -= np.mean(ydata)

                polygon = series_to_polyline(xdata, ydata)
                
                x_min = np.fmin(x_min, xdata.min())
                x_max = np.fmax(x_max, xdata.max())
                y_min = np.fmin(y_min, ydata.min())
                y_max = np.fmax(y_max, ydata.max())

                key = (dataSource, label)
                serie = self._series.get(key)
                if serie is None:
                    serie = self._series[key] = self._chart.createSeriesWithLabel(f"{dataSource}_{label}") # workaround: calling self.chart_.createSeries(...) returns None instead of a QLineSeries instance
                    serie.setColor(self._color_for(label))

                if serie.count() > 0:
                    serie.replace(polygon)
                else:
                    serie.append(polygon)

        if x_min > x_max:
            x_min, x_max = 0.0, 1.0
        if y_min > y_max:
            y_min, y_max = 0.0, 1.0

        self.set_xMin(self, x_min)
        self.set_xMax(self, x_max)
        self.set_yMin(self, y_min)
        self.set_yMax(self, y_max)