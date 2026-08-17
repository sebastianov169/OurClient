
undefined8 * FUN_14076eed0(undefined8 *param_1,undefined8 param_2,longlong *param_3)

{
  undefined8 *puVar1;
  char cVar2;
  undefined8 *local_res18 [2];
  
  cVar2 = FUN_140052590(local_res18,*param_3);
  if (cVar2 == '\0') {
    puVar1 = (undefined8 *)*param_3;
    if (puVar1 == (undefined8 *)0x0) {
      local_res18[0] = (undefined8 *)0x0;
    }
    else {
      cVar2 = (**(code **)*puVar1)(puVar1,0x20f64c9a);
      local_res18[0] = (undefined8 *)0x0;
      if (cVar2 != '\0') {
        local_res18[0] = puVar1;
      }
    }
  }
  FUN_14076c400(param_2,local_res18);
  *param_1 = 0;
  return param_1;
}

