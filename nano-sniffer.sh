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
sudo "$TSHARK" -i "usbmon${NANO_BUS}" -Y "usb.device_address == $NANO_DEV && usb.capdata" \
    -T fields \
    -e frame.time_epoch \
    -e usb.endpoint_address.direction \
    -e usb.capdata \
    > "$OUTPUT_FILENAME"

# Modify the data for easier reading
## Make a backup
mv "$OUTPUT_FILENAME" "${OUTPUT_FILENAME}-tmp"
## Add a header
echo -e "Timestamp\t\tDir\tData\n" > "${OUTPUT_FILENAME}"
## Loop over each line
while read -r line
do
    IFS=$'\t' read -r -a line_array <<< "$line"
    TIMESTAMP=$(date -d @"${line_array[0]}" +"%H:%M:%S:%N")
    DIRECTION=
    case "${line_array[1]}" in
        0)
            DIRECTION=OUT
            ;;
        1)
            DIRECTION=IN
            ;;
        *)
            echo "Unknown direction (${line_array[1]})" >&2
            ;;
    esac
    DATA="${line_array[2]}"
    echo -e "$TIMESTAMP\t$DIRECTION\t$DATA" >> "$OUTPUT_FILENAME"
done <"${OUTPUT_FILENAME}-tmp"
rm "${OUTPUT_FILENAME}-tmp"
