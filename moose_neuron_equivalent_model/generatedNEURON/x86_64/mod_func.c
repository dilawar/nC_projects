#include <stdio.h>
#include "hocdec.h"
extern int nrnmpi_myid;
extern int nrn_nobanner_;

extern void _CurrentClampExt_reg(void);
extern void _KConductance_reg(void);
extern void _LeakConductance_reg(void);
extern void _NaConductance_reg(void);
extern void _SynForRndSpike_reg(void);

void modl_reg(){
  if (!nrn_nobanner_) if (nrnmpi_myid < 1) {
    fprintf(stderr, "Additional mechanisms from files\n");

    fprintf(stderr," CurrentClampExt.mod");
    fprintf(stderr," KConductance.mod");
    fprintf(stderr," LeakConductance.mod");
    fprintf(stderr," NaConductance.mod");
    fprintf(stderr," SynForRndSpike.mod");
    fprintf(stderr, "\n");
  }
  _CurrentClampExt_reg();
  _KConductance_reg();
  _LeakConductance_reg();
  _NaConductance_reg();
  _SynForRndSpike_reg();
}
