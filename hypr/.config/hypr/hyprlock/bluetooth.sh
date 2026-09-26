#!/bin/bash

# Path to the Hyprland configuration file
config_file="$HOME/.config/hypr/hyprlock.conf"

# Read the bt-mode value from the configuration file
bt_mode=$(grep -oP '^\$bt-mode\s*=\s*\K\S+' ~/.config/hypr/hyprlock.conf)

# Get Bluetooth power status
bluetooth_status=$(bluetoothctl show | grep "Powered:" | awk '{print $2}')

# Check if Bluetooth is powered on
if [ "$bluetooth_status" != "yes" ]; then
    echo "󰂯 Bluetooth Off"
    exit 0
fi

# Initialize connected devices
connected_devices=""

# Process Bluetooth devices
while read -r line; do
    device_mac=$(echo "$line" | awk '{print $2}')
    device_name=$(echo "$line" | cut -d' ' -f3-)
    if bluetoothctl info "$device_mac" | grep -q "Connected: yes"; then
      connected_devices+="$device_name "
    fi
done < <(bluetoothctl devices)

connected_devices=${connected_devices% }

# If no connected devices, show "No Devices"
if [ -z "$connected_devices" ]; then
    echo "󰂲 No Devices"
    exit 0
fi

# Display output based on bt-mode
if [ "$bt_mode" = "true" ]; then
    echo "󰂯 $connected_devices"
else
    echo "󰂯 Connected"
fi
