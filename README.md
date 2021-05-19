# Simple FOC Scope


This project aim to analyse signals output by a SimpleFOC instance. 
It has a few main design goals:
* keep the amount of new code to add a new signal minimal (both client-side and MCU-side)
* use a C-language parsing library to parse C-headers containing structs to be sent directly on the communication link, whitout having to write more than a single new line of code (client nor MCU-side)
    * client: `headers: [..., "MyStruct.h"]`
    * MCU: `send("MyStructName", myStructInstance);`
* use ressources and bandwitdh efficiently (both client-side and MCU-side)
* use QML as a UI definition language and python as a control language and make the design modular so other users can use it as a library to create their own workbenches (No QWidget, no ui code in python)
* use PySide2/6 instead of PyQt5/6 and benefit from an LGPL license

