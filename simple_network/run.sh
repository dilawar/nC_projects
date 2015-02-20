#!/usr/bin/env bash
set -x
python ./simple_network.py -f \
    ./generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1 \
    -nc 30 -ns 100 -es 0.5 -sn 0.3 -bm 0.3 \
    -sw 0.005 -0.020 -st -0.055 -0.055 \
    -rt 2.0
