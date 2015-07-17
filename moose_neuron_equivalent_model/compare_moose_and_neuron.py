"""load_neuroml_in_neuron.py: 

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import moose
from neuron import h
import sys
import  networkx as nx
import pylab
import moose_channels as mc
import moose.utils as mu
from collections import defaultdict
import numpy as np

topology = nx.DiGraph()

records_ = { 't' : h.Vector() }
nrnsegs_ = {}
moosecompts_ = {}
cable_start_ = {}
nrnsecs_ = defaultdict(set)

moose.Neutral('/cell')

def loadNML(filename):
    h.load_file('stdgui.hoc')
    h.load_file('import3d.hoc')
    cell = h.Import3d_MorphML()
    cell.input(filename)
    i3d = h.Import3d_GUI(cell, 0)
    i3d.instantiate(None)
    return i3d

def addStim(soma):

    # This code does not work.
    #stim = h.IClamp(soma(0.5))
    #stim.amp = 1
    #stim.delay = 20
    #stim.dur = 60

    # This works. but delay does not work.
    h('access %s' % soma.hname())
    h('objectvar stim')
    h('stim = new IClamp(0.5)')
    h('stim.amp = 1')
    h('stim.del = 0')
    h('stim.dur = 100')

def simulate(t):
    h.load_file('stdrun.hoc')
    h.init()
    h.tstop = t * 1e3
    h.run()
    hsolve = moose.HSolve('/hsolve')
    hsolve.target = '/cell'
    hsolve.dt = 5e-5
    moose.reinit()
    moose.start(t)

def plot():
    pylab.subplot(2, 1, 1)
    pylab.plot(records_['t'], records_['soma'], label='neuron')
    clock = moose.Clock('/clock')
    yvec = records_['moose_soma'].vector
    pylab.subplot(2, 1, 2)
    pylab.plot(np.linspace(0, clock.currentTime, len(yvec)), yvec, label='moose') 
    pylab.legend(loc='best', framealpha=0.4)
    pylab.show()

def insertChannels(compt, nrnSeg):
    compt.length = nrnSeg.x * 1e-6
    compt.Em = nrnSeg.v * 1e-3
    compt.diameter = nrnSeg.diam * 1e-6
    na = mc.create_na_chan('%sn' % compt.path)
    sarea = np.pi * compt.diameter * compt.diameter
    compt.Rm = 1/(0.3e-3 * 1e4 * sarea)
    compt.Cm = 1e-6 * 1e4 * sarea
    na.Gbar = 120e-3 * sarea * 1e4
    compt.connect('channel', na, 'channel')
    k = mc.create_k_chan('%sk' % compt.path)
    k.Gbar = 36e-3 * sarea * 1e4
    compt.connect('channel', k, 'channel')

def createMOOSE():
    for i, v in enumerate(topology.nodes()):
        segname = topology.node[v]['label']
        comptPath = mooseName(segname)
        c = moose.Compartment(comptPath)
        moosecompts_[v] = comptPath
        insertChannels(c, v)
        print topology.in_degree(v), topology.out_degree(v), topology.degree(v)
        if topology.in_degree(v) == 0:
            mooseSoma = c

    for src, tgt in topology.edges(v):
        mooseA = moose.Compartment(moosecompts_[src])
        mooseB = moose.Compartment(moosecompts_[tgt])
        mooseA.connect('axial', mooseB, 'raxial')

    # apply current to mooseSoma
    #pulseGen = moose.PulseGen('/stim')
    #pulseGen.level[0] = 1e-10
    #pulseGen.delay[0] = 20e-3
    #pulseGen.width[0] = 60e-3
    #pulseGen.connect('output', mooseSoma, 'injectMsg')

    mooseSoma.inject = 1e-10

    table = moose.Table('/table_soma')
    table.connect('requestOut', mooseSoma, 'getVm')
    records_['moose_soma'] = table

def mooseName(n):
    mooseName = '/cell/%s' % n
    mooseName = mooseName.translate(None, '][')
    return mooseName

def main():
    filename = sys.argv[1]
    cell = loadNML(filename)
    soma = None

    # For each segment of cell, create a moose Compartment.
    totalSec = 0
    for sec in cell.allsec():
        totalSec +=  1
        secName = sec.hname()
        sec.insert('NaConductance')
        sec.insert('KConductance')

        cable = []
        assert sec.nseg > 0
        for i, seg in enumerate(sec.allseg()):
            assert seg
            segName = '%s%s' % (secName, i)
            print("Segment name: %s" % segName)
            cable.append(seg)
            topology.add_node(seg, label=segName, sec_name=secName) 
            nrnsecs_[sec].add(seg)
            nrnsegs_[seg] = sec
            if i > 0:
                topology.add_edge(cable[i-1], seg)
            else:
                cable_start_[secName] = seg

    # Get section from cell and draw edges.
    print("Total nodes in graph: %s" % topology.number_of_nodes())
    print("Total section in Neuron: %s" % totalSec)

    for sec in cell.allsec():
        parent = sec.parentseg()
        if parent:
            for i, seg in enumerate(sec.allseg()):
                # Just add one, rest the already connected as cable.
                topology.add_edge(parent, seg)
                break
        else:
            soma = sec

    createMOOSE()
    if soma:
        addStim(soma)
        records_['soma'] = h.Vector()
        records_['soma'].record(soma(0.5)._ref_v)
        records_['t'].record(h._ref_t)
    else:
        raise Exception("Couldn't find soma")

    simulate(0.1)
    plot()
    #nx.draw_graphviz(topology , prog='neato', with_labels=False)
    pylab.show()
    
if __name__ == '__main__':
    main()
