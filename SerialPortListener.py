from PySide6 import QtCore
from PySide6.QtCore import Signal, Slot
import logging
import threading
from PySide6.QtQuick import QQuickItem
from pyclibrary import CParser
import numpy as np
import ctypes
import time  
import serial
import Product
import SimpleFOCScope

class SimpleFOCSerialScope(QQuickItem):
    def __init__(self, parent = None):
        super(SimpleFOCSerialScope, self).__init__(parent)
        
        self._port = ""
        self._bauds = ""
        self._traces = None
        self._headers = ['demo.h']
        self.connector = SerialPortListener()
        self.connector.parseHeaders(self.headers)


    def cb_traces(self, old_value):
        if self._traces is not None:
            if old_value is not None:
                self.connector.dataReceived.disconnect(old_value.dataReceived)
            
            self.connector.dataReceived.connect(self._traces.dataReceived)
        pass

    Product.RWProperty(vars(), SimpleFOCScope.SimpleFOCScope , "traces", cb_traces)

    Product.RWProperty(vars(), str , "port")
    Product.RWProperty(vars(), int , "bauds")

    def cb_headers(self, old_value):
        self.connector.parseHeaders(self.headers)

    Product.RWProperty(vars(), list , "headers", cb_headers)

    @Slot()
    def beginListneing(self):
        try:
            serial_port = serial.Serial(self.port, self.bauds, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE)
            if not serial_port.isOpen():
                serial_port = None
        except:
            serial_port = None
        self.connector.beginListneing(serial_port)


class SimpleFOCParsingException(Exception):
    def __init__(self, type):
        super(Exception, self).__init__(f'Type {type} not reckognized')
        self.type = type


class SerialPortListener(QtCore.QThread):

    dataReceived = Signal(str, np.ndarray)

    def __init__(self):
        super(SerialPortListener, self).__init__()
        self._stop_event = threading.Event()
        self._serial_port = None
        self.parser = None
        self.dtypes = {}
    
    def parseHeaders(self, headers):
        
        self.parser = CParser(headers)
        self.dtypes = {}
        for (struct_name, s) in self.parser.defs['structs'].items():
            members = s['members']
            for (name, type, default_Value) in members:
                c_typename = type[0]
                if c_typename in self.parser.defs['structs'] and c_typename not in self.dtypes:
                    self.add_type(c_typename, self.parser.defs['structs'][c_typename])

            self.add_dtype(struct_name, members)
        
    def beginListneing(self, serial_port = None):
        self._serial_port = serial_port
        self.start()

    def add_dtype(self, struct_name, members):
        if struct_name not in self.dtypes:
            np_type = np.dtype([self.to_dtype(name, type) for (name, type, default_Value) in members])
            self.dtypes[struct_name] = np_type


    def to_dtype(self, name, type):
        c_typename = type[0]
        n = 0
        if c_typename in self.dtypes:
            return (name, self.dtypes[c_typename])

        if c_typename.endswith("_t"): #e.g. uint18_t -> uint8
            c_typename = c_typename[:-2]

        try:
            ctype = getattr(ctypes, f"c_{c_typename}")
        except:
            raise SimpleFOCParsingException(type)

        if len(type) > 1:
            return (name, ctype, type[1][0])
        
        return (name, ctype)

    def handle_received_data(self, header_string, data, header_dtype):
        try:
            b = np.frombuffer(data, header_dtype)
            self.dataReceived.emit(header_string, b)

        except Exception as e:
            logging.error(e, exc_info=True)

    def match_header(self, header):
        if header in self.dtypes:
            return self.dtypes[header]

        logging.warning(f"Header '{header}' not reckognized")
        
        return None

    def run(self):
        try:
            while not self.stopped():
                if self._serial_port is not None:
                    if self._serial_port.isOpen():
                        header_dtype = None
                        
                        while True:
                            header_string = self._serial_port.readline().rstrip().decode("ascii")
                            if header_string:
                                header_dtype = self.match_header(header_string)
                            if header_dtype is not None :
                                break
                        data = self._serial_port.read(header_dtype.itemsize)
                        self.handle_received_data(header_string, data, header_dtype)
                else:
                    t = time.time()
                    dtype = self.dtypes["Demo"]
                    self.dataReceived.emit("Demo", np.array([(np.sin(t), np.cos(t))], dtype ))
                    self.msleep(1)
                        
        except serial.SerialException as serialException:
            logging.error(serialException, exc_info=True)
        except TypeError as typeError:
            logging.error(typeError, exc_info=True)
        except AttributeError as ae:
            logging.error(ae, exc_info=True)
        except Exception as e:
             logging.error(e, exc_info=True)          

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

