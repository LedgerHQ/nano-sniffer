#!/usr/bin/env bash

NANO_LINE=$(lsusb | grep 'Ledger Nano' | cut -d: -f1)

# check if connected
if [ -z "$NANO_LINE" ]
then
    echo "USB Nano device not detected" >&2
    exit 1
fi

NANO_BUS=$(echo "$NANO_LINE" | cut -d' ' -f2 | bc)
NANO_DEV=$(echo "$NANO_LINE" | cut -d' ' -f4 | bc)

# check if kernel module is loaded
if ! lsmod | grep -q usbmon
then
    echo "Kernel module not loaded, loading now..."
    sudo modprobe usbmon
fi

OUTPUT_FILENAME="capture_$(date +%s).txt"

trap print_filename INT

print_filename()
{
    echo "==> saved in $OUTPUT_FILENAME"
}

TSHARK=tshark

if ! command -v "$TSHARK" > /dev/null
then
    echo "$TSHARK not detected, please install it" >&2
    exit 1
fi

# shellcheck disable=2024
sudo "$TSHARK" -i "usbmon${NANO_BUS}" -Y "usb.device_address == $NANO_DEV && usb.capdata" -T fields -e usb.endpoint_address.direction -e usb.capdata > "$OUTPUT_FILENAME"

# Modify the data for easier reading
## Interpret the direction value
sed 's/^0/OUT/g' -i "$OUTPUT_FILENAME"
sed 's/^1/IN/g' -i "$OUTPUT_FILENAME"
## Add a header
echo -e "Dir\tRaw data\n" > "${OUTPUT_FILENAME}-tmp"
cat "$OUTPUT_FILENAME" >> "${OUTPUT_FILENAME}-tmp"
mv "${OUTPUT_FILENAME}-tmp" "$OUTPUT_FILENAME"
