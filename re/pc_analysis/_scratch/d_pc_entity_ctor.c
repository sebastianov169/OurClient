
undefined8 * FUN_14183d390(undefined8 *param_1,longlong *param_2,undefined8 *param_3)

{
  undefined8 local_res10 [3];
  
  param_2 = (longlong *)*param_2;
  if (param_2 != (longlong *)0x0) {
    local_res10[0] = 0;
    FUN_1400294a0(local_res10,*param_3);
    (**(code **)(*param_2 + 0x108))(param_2,param_1,local_res10);
    return param_1;
  }
  *param_1 = 0;
  return param_1;
}

