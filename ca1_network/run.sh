#!/usr/bin/env bash
set -x
python ./simple_network.py -f \
    ./ca1_network/CA1.morph.xml \
    -nc 30 -ns 100 -es 0.5 -sn 0.3 -bm 0.3 \
    -sw 0.005 -0.020 -st -0.055 -0.055 \
    -rt 0.1
