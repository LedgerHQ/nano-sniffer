#!/usr/bin/env python3

import os
import subprocess
# Dependencies
import pyshark
import usb.core


if os.geteuid() != 0:
    print('Error: root required !')
    exit(1)

dev = usb.core.find(idVendor=0x2c97)
if dev is None:
    print('Error: No Nano found !')
    exit(1)

print('Nano found on Bus %d, Device %d' % (dev.bus, dev.address))

# Load necessary kernel module (does nothing if already loaded)
subprocess.call(['modprobe', 'usbmon'])

capture = pyshark.LiveCapture(interface='usbmon%d' % (dev.bus),
                              display_filter='usb.device_address == %d && usb.capdata' % (dev.address))

for packet in capture.sniff_continuously():
    timestamp = None
    direction = None
    data = None

    try:
        if (int(packet.usb.endpoint_address_direction) == 0):
            direction = 'OUT'
        else:
            direction = 'IN'
        data = packet.data.usb_capdata.split(":")
        print('%s\t%s\t%s' % (packet.sniff_time, direction, str(data)))
    except:
        pass
