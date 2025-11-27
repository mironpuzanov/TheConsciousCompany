#!/bin/bash

# Wrapper script to continuously retry muselsl stream connection
# This keeps searching for Muse until you connect via web interface

echo "🔍 Starting Muse LSL retry loop..."
echo "   Will continuously search for Muse headband until connected"
echo ""

while true; do
    echo "[$(date '+%H:%M:%S')] Searching for Muse headband..."
    muselsl stream --ppg --acc --gyro

    # If muselsl exits, wait a bit and retry
    echo "[$(date '+%H:%M:%S')] Muse connection lost or not found. Retrying in 5 seconds..."
    sleep 5
done
