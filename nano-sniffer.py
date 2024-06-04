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
        except Exception:
            pass


if os.geteuid() != 0:
    print('Error: root required !')
    exit(1)

# Data offset
APDU_DATA_MAGIC_OFFSET = 2
APDU_DATA_LENGTH_OFFSET = 5
APDU_DATA_OFFSET_FIRST = 7
APDU_DATA_OFFSET_FOLLW = 5

# Tag value
APDU_TAG_GET_VERSION_ID = 0x00
APDU_TAG_ALLOCATE_CHANNEL = 0x01
APDU_TAG_ECHO_PING = 0x02
APDU_TAG_DEFAULT = 0x5


dev = usb.core.find(idVendor=0x2c97)
if dev is None:
    print('Error: No Nano found !')
    exit(1)

print('Nano found on Bus %d, Device %d' % (dev.bus, dev.address))

# Load necessary kernel module (does nothing if already loaded)
subprocess.call(['modprobe', 'usbmon'])

capture = pyshark.LiveCapture(interface='usbmon0',
                              display_filter='usb.device_address == %d && usb.capdata' % (dev.address))

signal.signal(signal.SIGINT, sigint_handler)

apdu_buffer = []
apdu_length = 0

for packet in capture.sniff_continuously():
    timestamp = None
    direction = None
    data = None
    tag = None

    try:
        if (int(packet.usb.endpoint_address_direction) == 0):
            direction = '=>'
        else:
            direction = '<='

        data = packet.data.usb_capdata.split(":")

        tag = int(data[APDU_DATA_MAGIC_OFFSET], 16)
        # Sanity check (something is very wrong if this check fails)
        if tag not in (APDU_TAG_GET_VERSION_ID,
                       APDU_TAG_ALLOCATE_CHANNEL,
                       APDU_TAG_ECHO_PING,
                       APDU_TAG_DEFAULT):
            print("Error unexpected value at tag offset! (0x%x)\n" % (tag))
            break

        # First chunk of an apdu
        if (len(apdu_buffer) == 0):
            apdu_length = int(data[APDU_DATA_LENGTH_OFFSET], 16) << 8 | \
                          int(data[APDU_DATA_LENGTH_OFFSET + 1], 16)
            apdu_buffer += data[APDU_DATA_OFFSET_FIRST:(APDU_DATA_OFFSET_FIRST + apdu_length)]

        # Following chunk(s) of an apdu
        else:
            apdu_buffer += data[APDU_DATA_OFFSET_FOLLW:(APDU_DATA_OFFSET_FOLLW + (apdu_length - len(apdu_buffer)))]

        if (len(apdu_buffer) == apdu_length):
            print('[%s] HID %s %s' % (packet.sniff_time, direction, "".join(apdu_buffer)))
            # Reset states, so we treat the next chunk as a first one again
            apdu_buffer = []
            apdu_length = 0
    except Exception:
        pass
