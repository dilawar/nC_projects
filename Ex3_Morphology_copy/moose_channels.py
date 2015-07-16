import moose

EREST_ACT = -70e-3

# Gate equations have the form:
#
# y(x) = (A + B * x) / (C + exp((x + D) / F))
# 
# where x is membrane voltage and y is the rate constant for gate
# closing or opening

Na_m_params = [1e5 * (25e-3 + EREST_ACT),   # 'A_A':
                -1e5,                       # 'A_B':
                -1.0,                       # 'A_C':
                -25e-3 - EREST_ACT,         # 'A_D':
               -10e-3,                      # 'A_F':
                4e3,                     # 'B_A':
                0.0,                        # 'B_B':
                0.0,                        # 'B_C':
                0.0 - EREST_ACT,            # 'B_D':
                18e-3                       # 'B_F':    
               ]
Na_h_params = [ 70.0,                        # 'A_A':
                0.0,                       # 'A_B':
                0.0,                       # 'A_C':
                0.0 - EREST_ACT,           # 'A_D':
                0.02,                     # 'A_F':
                1000.0,                       # 'B_A':
                0.0,                       # 'B_B':
                1.0,                       # 'B_C':
                -30e-3 - EREST_ACT,        # 'B_D':
                -0.01                    # 'B_F':       
                ]        
K_n_params = [ 1e4 * (10e-3 + EREST_ACT),   #  'A_A':
               -1e4,                      #  'A_B':
               -1.0,                       #  'A_C':
               -10e-3 - EREST_ACT,         #  'A_D':
               -10e-3,                     #  'A_F':
               0.125e3,                   #  'B_A':
               0.0,                        #  'B_B':
               0.0,                        #  'B_C':
               0.0 - EREST_ACT,            #  'B_D':
               80e-3                       #  'B_F':  
               ]
VMIN = -40e-3 + EREST_ACT
VMAX = 120e-3 + EREST_ACT
VDIVS = 30000

soma_dia = 30e-6

def create_na_chan(path):
    na = moose.HHChannel('%s/na' % (path))
    na.Xpower = 3
    xGate = moose.HHGate(na.path + '/gateX')    
    xGate.setupAlpha(Na_m_params +
                      [VDIVS, VMIN, VMAX])
    na.Ypower = 1
    yGate = moose.HHGate(na.path + '/gateY')
    yGate.setupAlpha(Na_h_params + 
                      [VDIVS, VMIN, VMAX])
    na.Ek = 115e-3 + EREST_ACT
    return na

def create_k_chan(path):
    k = moose.HHChannel('%s/k' % (path))
    k.Xpower = 4.0
    xGate = moose.HHGate(k.path + '/gateX')    
    xGate.setupAlpha(K_n_params +
                      [VDIVS, VMIN, VMAX])
    k.Ek = -12e-3 + EREST_ACT
    return k

def create_compartment(path):
    comp = moose.Compartment(path)
    comp.diameter = soma_dia
    comp.Em = EREST_ACT + 10.613e-3
    comp.initVm = EREST_ACT
    sarea = np.pi * soma_dia * soma_dia
    comp.Rm = 1/(0.3e-3 * 1e4 * sarea)
    comp.Cm = 1e-6 * 1e4 * sarea
    if moose.exists('/library/na'):
        nachan = moose.element(moose.copy('/library/na', comp, 'na'))
    else:
        nachan = create_na_chan(comp.path)
    nachan.Gbar = 120e-3 * sarea * 1e4
    moose.showfield(nachan)
    moose.connect(nachan, 'channel', comp, 'channel')
    if moose.exists('/library/k'):
        kchan = moose.element(moose.copy('/library/k', comp, 'k'))
    else:
        kchan = create_k_chan(comp.path)
    kchan.Gbar = 36e-3 * sarea * 1e4
    moose.connect(kchan, 'channel', comp, 'channel')
    synchan = moose.SynChan(comp.path + '/synchan')
    synchan.Gbar = 1e-8
    synchan.tau1 = 2e-3
    synchan.tau2 = 2e-3        
    synchan.Ek = 0.0
    m = moose.connect(comp, 'channel', synchan, 'channel')
    spikegen = moose.SpikeGen(comp.path + '/spikegen')
    spikegen.threshold = 0.0
    m = moose.connect(comp, 'VmOut', spikegen, 'Vm')
    return comp

def test_compartment():
    n = moose.Neutral('/model')
    lib = moose.Neutral('/library')
    create_na_chan(lib.path)
    create_k_chan(lib.path)
    comp = create_compartment('/model/soma')
    pg = moose.PulseGen('/model/pulse')
    pg.firstDelay = 50e-3
    pg.firstWidth = 40e-3
    pg.firstLevel = 1e-9
    moose.connect(pg, 'output', comp, 'injectMsg')
    d = moose.Neutral('/data')
    vm = moose.Table('/data/Vm')
    moose.connect(vm, 'requestOut', comp, 'getVm')
    gK = moose.Table('/data/gK')
    moose.connect(gK, 'requestOut', moose.element('%s/k' % (comp.path)), 'getGk')
    gNa = moose.Table('/data/gNa')
    moose.connect(gNa, 'requestOut', moose.element('%s/na' % (comp.path)), 'getGk')
    # utils.resetSim(['/model', '/data'], 1e-6, 1e-4, simmethod='ee')
    assign_clocks(['/model'], 1e-6, 1e-4)
    simtime = 100e-3
    moose.start(simtime)
    t = np.linspace(0, simtime, len(vm.vector))
    plt.subplot(221)
    plt.title('Vm')
    plt.plot(t, vm.vector)
    plt.subplot(222)
    plt.title('Conductance')
    plt.plot(t, gK.vector, label='GK')
    plt.plot(t, gNa.vector, label='GNa')
    plt.legend()
    plt.subplot(223)
    ma = moose.element('%s/na/gateX' % (comp.path)).tableA
    mb = moose.element('%s/na/gateX' % (comp.path)).tableB
    ha = moose.element('%s/na/gateY' % (comp.path)).tableA
    hb = moose.element('%s/na/gateY' % (comp.path)).tableB
    na = moose.element('%s/k/gateX' % (comp.path)).tableA
    nb = moose.element('%s/k/gateX' % (comp.path)).tableB
    plt.plot(1/mb, label='tau_m')
    plt.plot(1/hb, label='tau_h')
    plt.plot(1/nb, label='tau_n')
    plt.legend()
    plt.subplot(224)
    plt.plot(ma/mb, label='m_inf')
    plt.plot(ha/hb, label='h_inf')
    plt.plot(na/nb, label='n_inf')
    plt.legend()
    plt.show()
    plt.close()

# compartment_net_no_array.py ends here
