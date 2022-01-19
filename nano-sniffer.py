#!/usr/bin/env python3

import os
import subprocess
import signal
# Dependencies
import pyshark
import usb.core
import psutil


# pyshark have had issues with subprocesses not properly closing for years
def sigint_handler(signum, frame):
    # get the script's own pid
    pid_self = psutil.Process(os.getpid())
    # get all the list of subprocesses
    children = pid_self.children(recursive=True)
    # kill each of them (only signal 9 seems to work for tshark)
    for child in children:
        try:
            child.send_signal(signal.SIGKILL)
        except:
            pass


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

signal.signal(signal.SIGINT, sigint_handler)

for packet in capture.sniff_continuously():
    timestamp = None
    direction = None
    data = None

    try:
        if (int(packet.usb.endpoint_address_direction) == 0):
            direction = '=>'
        else:
            direction = '<='
        data = packet.data.usb_capdata.split(":")
        packet_length = int(data[6], 16)
        print('[%s] HID %s %s' % (packet.sniff_time, direction, "".join(data[7:7+packet_length])))
    except:
        pass
