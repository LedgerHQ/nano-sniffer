#!/usr/bin/env python3

# Dependencies
import pyshark
import usb.core


dev = usb.core.find(idVendor=0x2c97)
if dev is None:
    print("Error: No Nano found !")
    exit(1)

print("Nano found on Bus %d, Device %d" % (dev.bus, dev.address))

capture = pyshark.LiveCapture(interface='usbmon%d' % (dev.bus),
                              display_filter='usb.device_address == %d && usb.capdata' % (dev.address))

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
