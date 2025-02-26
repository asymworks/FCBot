#!/bin/bash

export PYTHONPATH=/app

echo "======================================================"
echo "                                                      "
echo "  ________ ________  ________  ________  _________    "
echo " |\  _____\\\\   ____\|\   __  \|\   __  \|\___   ___\  "
echo " \ \  \__/\ \  \___|\ \  \|\ /\ \  \|\  \|___ \  \_|  "
echo "  \ \   __\\\\ \  \    \ \   __  \ \  \\\\\\  \   \ \  \   "
echo "   \ \  \_| \ \  \____\ \  \|\  \ \  \\\\\\  \   \ \  \  "
echo "    \ \__\   \ \_______\ \_______\ \_______\   \ \__\ "
echo "     \|__|    \|_______|\|_______|\|_______|    \|__| "
echo "                                                      "
echo "======================================================"
echo 
echo "FreeCAD CI/CD Action v1"
echo
echo "Entering FCBot Virtual Environment"
source /app/.venv/bin/activate

echo
echo "Version Information"
echo "  $(freecadcmd -v)"
echo "  FreeCAD Python $(freecadcmd /app/py_version.py | head -n1)"
echo "  $(uv run python3 -m fcbot -V)"
echo "Starting Xvfb"

XVFB_RES=${XVFB_RES:-1024x768x24}
Xvfb :99 -ac -screen 0 "${XVFB_RES}" -nolisten tcp $XVFB_ARGS &
XVFB_PROC=$!
sleep 1

echo "Starting FCBot"
echo
export DISPLAY=:99
uv run python3 -m fcbot $@

echo
echo "Stopping Xvfb"
kill $XVFB_PROC
