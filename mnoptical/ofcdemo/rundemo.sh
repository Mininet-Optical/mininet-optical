#!/bin/bash -x

# Note: the simpler 3-node linear topology has been
# moved to simpledemo.py

echo '*** Running demo script'
sudo PYTHONPATH=../..:. python ./demo.py
