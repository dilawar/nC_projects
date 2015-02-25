#!/usr/bin/env bash
set -x
#rm -rf *.png
python ./network_nml2.py -f \
    ./../simple_cell/generatedNeuroML2/SampleCell.cell.nml \
    -nc 20 -ns 100\
    -es 1.0 -sn 0.2 -bm 0.0 \
    -sw 0.1 -0.0050 -st -0.055 -0.055 \
    -rt 0.1

#if [ -f network.dot ]; then
#    echo "graphviz"
#    neato -Tpng network.dot > network.png
#fi
