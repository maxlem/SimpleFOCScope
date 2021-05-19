# This Python file uses the following encoding: utf-8
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QUrl
from PySide6.QtQml import qmlRegisterType, QQmlApplicationEngine
from PySide6.QtCore import Slot
import SerialPortListener
import SimpleFOCScope


qmlRegisterType(SerialPortListener.SimpleFOCSerialScope, "SimpleFOC", 1, 0, "SimpleFOCSerialScope")
qmlRegisterType(SimpleFOCScope.SimpleFOCScope, "SimpleFOC", 1, 0, "SimpleFOCScope")
if __name__ == "__main__":

    app = QApplication(sys.argv) # <---

    engine = QQmlApplicationEngine()
    engine.load(QUrl("main.qml"))

    if not engine.rootObjects():
        sys.exit(-1)

    win = engine.rootObjects()[0]
    win.show()
    sys.exit(app.exec())
