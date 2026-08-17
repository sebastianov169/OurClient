
void FUN_140679380(longlong *param_1,longlong param_2,longlong param_3,double param_4)

{
  param_1[0x17] = (longlong)param_4;
  param_1[0x15] = param_2;
  param_1[0x16] = param_3;
  (**(code **)(*param_1 + 0x1b8))(param_1,SUB84(param_4 / 1000.0,0));
  FUN_140678360(param_1,(int)param_2,(int)param_3);
  return;
}

