import glob
import struct
import time

import serial

PACKET_HEADER = b'ScopeData\n'
PACKET_SIZE = 56
PACKET = struct.Struct('<Q7HHI7f')

port = glob.glob('/dev/serial/by-id/*Feather_M4_CAN*')[0]
ser = serial.Serial(port, 115200, timeout=0.1)
ser.reset_input_buffer()
buf = b''
packets = []
end = time.time() + 2.0
while time.time() < end:
    buf += ser.read(512)
    while True:
        i = buf.find(PACKET_HEADER)
        if i < 0 or len(buf) < i + len(PACKET_HEADER) + PACKET_SIZE:
            break
        start = i + len(PACKET_HEADER)
        raw = buf[start:start + PACKET_SIZE]
        buf = buf[start + PACKET_SIZE:]
        packets.append(PACKET.unpack(raw))
ser.close()
print('port:', port)
print('packets:', len(packets))
if packets:
    for idx, name in enumerate(['ia', 'ib', 'ic', 'va', 'vb', 'vc', 'vm']):
        values = [p[10 + idx] for p in packets]
        print(f'{name}: last={values[-1]:.4f} min={min(values):.4f} max={max(values):.4f}')
