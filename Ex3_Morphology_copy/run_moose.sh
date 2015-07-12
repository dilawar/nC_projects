#!/bin/bash
set -e
rm -f ./soma.png
python ./load_neuroml_in_moose.py ./generatedNeuroML/Generated.net.xml | tee _moose.log
if [ -f soma.png ]; then
    display ./soma.png
fi
