
void FUN_1406775f0(longlong *param_1,double param_2,double param_3)

{
  int iVar1;
  double dVar2;
  
  dVar2 = (1.0 - param_3) * (double)param_1[0x18] + param_2 * param_3;
  if ((dVar2 < -2147483647.0) || (2147483647.0 < dVar2)) {
    iVar1 = (int)(longlong)dVar2;
  }
  else {
    iVar1 = (int)dVar2;
  }
  if (iVar1 != (int)param_1[0x12]) {
    if ((param_2 < -2147483647.0) || (2147483647.0 < param_2)) {
      iVar1 = (int)(longlong)param_2;
    }
    else {
      iVar1 = (int)param_2;
    }
    *(int *)(param_1 + 0x12) = iVar1;
    dVar2 = (double)FUN_141bf6990((double)iVar1);
    dVar2 = floor(dVar2 * 10.0 + 0.5);
    if ((dVar2 < -2147483647.0) || (2147483647.0 < dVar2)) {
      iVar1 = (int)(longlong)dVar2;
    }
    else {
      iVar1 = (int)dVar2;
    }
    (**(code **)(*param_1 + 0x1c8))(param_1,(double)(iVar1 + 1));
    (**(code **)(*param_1 + 0x140))(param_1);
  }
  return;
}

