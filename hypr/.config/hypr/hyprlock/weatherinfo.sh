#!/bin/bash

# Privacy first: never geolocate the public IP. Weather is opt-in by setting
# $CITY and optionally $COUNTRY in hyprlock.conf.
config_file="$HOME/.config/hypr/hyprlock.conf"
city=$(sed -n 's/^\$CITY[[:space:]]*=[[:space:]]*//p' "$config_file" | head -n 1)
country=$(sed -n 's/^\$COUNTRY[[:space:]]*=[[:space:]]*//p' "$config_file" | head -n 1)

[ -n "$city" ] || exit 0
command -v curl >/dev/null 2>&1 || exit 0

weather_info=$(curl --fail --silent --show-error --max-time 5 \
  --get --data-urlencode "format=%c %C %t" "https://wttr.in/$city" 2>/dev/null) || exit 0

if [ -n "$country" ]; then
  printf '%s, %s: %s\n' "$country" "$city" "$weather_info"
else
  printf '%s: %s\n' "$city" "$weather_info"
fi
