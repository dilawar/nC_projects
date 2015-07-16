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

from neuron import h
import sys

records_ = { 't' : h.Vector() }

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
    h('stim.del = 20')
    h('stim.dur = 60')

def simulate(t):
    h.load_file('stdrun.hoc')
    h.init()
    h.tstop = t * 1e3
    h.run()

def plot():
    import pylab
    pylab.plot(records_['t'], records_['soma'])
    pylab.show()


def main():
    filename = sys.argv[1]
    cell = loadNML(filename)
    soma = None
    for i, sec in enumerate(cell.allsec()):
        sec.insert('NaConductance')
        sec.insert('KConductance')
        if sec.parentseg() is None:
            soma = sec
    if soma:
        addStim(soma)
        records_['soma'] = h.Vector()
        records_['soma'].record(soma(0.5)._ref_v)
        records_['t'].record(h._ref_t)
    else:
        raise Exception("Couldn't find soma")

    simulate(0.1)
    plot()
    
if __name__ == '__main__':
    main()
