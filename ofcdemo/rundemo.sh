#!/bin/bash -x

# echo '*** Cleaning up stale mininet instances'
# sudo mn -c

echo '*** Running demo script'
sudo PYTHONPATH=..:. python ./demo.py
