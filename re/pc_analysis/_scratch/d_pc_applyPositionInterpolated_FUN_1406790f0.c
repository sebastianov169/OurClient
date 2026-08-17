
void FUN_1406790f0(longlong *param_1,double param_2,double param_3,double param_4,double param_5)

{
  double dVar1;
  double dVar2;
  double dVar3;
  double dVar4;
  double dVar5;
  
  dVar1 = (double)param_1[0x16];
  dVar2 = (double)param_1[0x15];
  for (dVar3 = (double)FUN_141bf552c((double)param_1[0x17] / 1000.0,0x401921fb54442d18); dVar3 < 0.0
      ; dVar3 = dVar3 + 6.283185307179586) {
  }
  for (dVar4 = (double)FUN_141bf552c(param_4 / 1000.0,0x401921fb54442d18); dVar4 < 0.0;
      dVar4 = dVar4 + 6.283185307179586) {
  }
  dVar5 = dVar4 - dVar3;
  if (dVar5 < -3.141592653589793) {
    dVar4 = dVar4 + 6.283185307179586;
  }
  if (3.141592653589793 < dVar5) {
    dVar4 = dVar4 + -6.283185307179586;
  }
  for (dVar3 = (double)FUN_141bf552c((dVar4 - dVar3) * param_5 + dVar3,0x401921fb54442d18);
      dVar3 < 0.0; dVar3 = dVar3 + 6.283185307179586) {
  }
  (**(code **)(*param_1 + 0x1b8))(param_1,(dVar3 * 1000.0) / 1000.0);
  FUN_140678360(param_1,(1.0 - param_5) * dVar2 + param_2 * param_5,
                (1.0 - param_5) * dVar1 + param_3 * param_5);
  return;
}

