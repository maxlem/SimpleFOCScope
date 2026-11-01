import glob
import struct
import time

import serial

PACKET_SIZE = 56
PACKET = struct.Struct('<Q7HHI7f')

port = glob.glob('/dev/serial/by-id/*Feather_M4_CAN*')[0]
ser = serial.Serial(port, 115200, timeout=0.1)
ser.reset_input_buffer()
buf = b''
packets = []
end = time.time() + 6.0
while time.time() < end:
    buf += ser.read(512)
    while b'\n' in buf:
        line, buf = buf.split(b'\n', 1)
        text = line.strip()
        if text == b'ScopeData':
            while len(buf) < PACKET_SIZE:
                buf += ser.read(PACKET_SIZE - len(buf))
            raw = buf[:PACKET_SIZE]
            buf = buf[PACKET_SIZE:]
            packets.append(PACKET.unpack(raw))
            continue
        try:
            printable = text.decode('ascii')
        except UnicodeDecodeError:
            continue
        if printable:
            print('TEXT:', printable)
ser.close()
print('packets:', len(packets))
if packets:
    for idx, name in enumerate(['ia', 'ib', 'ic', 'va', 'vb', 'vc', 'vm']):
        values = [p[10 + idx] for p in packets]
        print(f'{name}: last={values[-1]:.4f} min={min(values):.4f} max={max(values):.4f}')
