
void FUN_140678360(longlong *param_1,undefined4 param_2,undefined4 param_3)

{
  FUN_1413220b0(param_1[0xb]);
  FUN_1413222a0(param_1[0xb],param_3);
  if (param_1[0xc] != 0) {
    FUN_1413220b0(param_1[0xc],param_2);
    FUN_1413222a0(param_1[0xc],param_3);
  }
                    /* WARNING: Could not recover jumptable at 0x0001406783c0. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (**(code **)(*param_1 + 0x168))(param_1);
  return;
}

