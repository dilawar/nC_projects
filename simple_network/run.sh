#!/usr/bin/env bash
set -x
#rm -rf *.png
python ./simple_network.py -f \
    ./generatedNeuroML/L3Net_17-Feb-15_16-16-18.nml1 \
    -nc 5 -ns 10 \
    -es 0.7 -sn 0.2 -bm 0.0 \
    -sw 0.001 -0.0050 -st -0.055 -0.055 \
    -rt 0.5
if [ -f network.dot ]; then
    neato -Tpng network.dot > network.png
fi
