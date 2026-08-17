
void FUN_1414e2900(longlong param_1)

{
  double dVar1;
  double dVar2;
  double dVar3;
  double dVar4;
  double dVar5;
  double dVar6;
  double dVar7;
  double dVar8;
  
  dVar1 = *(double *)(param_1 + 0x2c8);
  dVar6 = *(double *)(param_1 + 0x2b0) * 0.5;
  dVar4 = dVar1 + *(double *)(DAT_1421c2a08 + 0x20);
  dVar8 = dVar1 + *(double *)(DAT_1421c2a08 + 0x18);
  dVar7 = *(double *)(DAT_1421c2a08 + 0x10) - (dVar1 + dVar1);
  dVar5 = *(double *)(DAT_1421c2a08 + 8) - (dVar1 + dVar1);
  dVar1 = dVar6 + dVar6 + dVar7;
  (**(code **)(**(longlong **)(param_1 + 0x288) + 0x1b0))(*(longlong **)(param_1 + 0x288),dVar1);
  dVar2 = dVar8 - dVar6;
  (**(code **)(**(longlong **)(param_1 + 0x288) + 0x1c8))(*(longlong **)(param_1 + 0x288),dVar2);
  dVar3 = dVar4 - dVar6;
  (**(code **)(**(longlong **)(param_1 + 0x288) + 0x1d0))(*(longlong **)(param_1 + 0x288),dVar3);
  (**(code **)(**(longlong **)(param_1 + 0x290) + 0x1b0))(*(longlong **)(param_1 + 0x290),dVar1);
  (**(code **)(**(longlong **)(param_1 + 0x290) + 0x1c8))(*(longlong **)(param_1 + 0x290),dVar2);
  (**(code **)(**(longlong **)(param_1 + 0x290) + 0x1d0))
            (*(longlong **)(param_1 + 0x290),(dVar5 + dVar4) - dVar6);
  dVar5 = dVar6 + dVar6 + dVar5;
  (**(code **)(**(longlong **)(param_1 + 0x298) + 0x1c0))(*(longlong **)(param_1 + 0x298),dVar5);
  (**(code **)(**(longlong **)(param_1 + 0x298) + 0x1d0))(*(longlong **)(param_1 + 0x298),dVar3);
  (**(code **)(**(longlong **)(param_1 + 0x298) + 0x1c8))(*(longlong **)(param_1 + 0x298),dVar2);
  (**(code **)(**(longlong **)(param_1 + 0x2a0) + 0x1c0))(*(longlong **)(param_1 + 0x2a0),dVar5);
  (**(code **)(**(longlong **)(param_1 + 0x2a0) + 0x1d0))(*(longlong **)(param_1 + 0x2a0),dVar3);
                    /* WARNING: Could not recover jumptable at 0x0001414e2ae6. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(**(longlong **)(param_1 + 0x2a0) + 0x1c8))
            (*(longlong **)(param_1 + 0x2a0),(dVar7 + dVar8) - dVar6);
  return;
}

