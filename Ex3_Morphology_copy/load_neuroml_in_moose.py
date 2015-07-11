#!/usr/bin/env python

import sys
import moose
import moose.neuroml as nml

def main():
    filename = sys.argv[1]
    print("Loading into MOOSE: %s" % filename)
    nml.loadNeuroML_L123(filename)
    tables = moose.wildcardFind('/##[TYPE=Table]')
    print tables
    moose.reinit()
    moose.start(1)

if __name__ == '__main__':
    main()
