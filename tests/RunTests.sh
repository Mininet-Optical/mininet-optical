#!/bin/bash
#Set Necissary Python paths for execution

set -e
#export PYTHONPATH=$PWD
export PYTHONPATH=..
echo "______update_rule_roadm.py______"
python update_rule_roadm.py
echo "______singlelinktests-ports.py______"
python singlelinktests-ports.py
echo "______multi_signal_transmissionports.py______"
python multi_signal_transmission.py
# echo -e "$?"
