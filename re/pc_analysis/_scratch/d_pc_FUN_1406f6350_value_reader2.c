
undefined8 FUN_1406f6350(undefined8 param_1,longlong param_2,longlong *param_3)

{
  undefined8 *puVar1;
  char cVar2;
  int iVar3;
  undefined8 *puVar4;
  float local_res18;
  undefined4 uStackX_1c;
  
  cVar2 = FUN_140052590(&local_res18,*param_3);
  if (cVar2 == '\0') {
    puVar1 = (undefined8 *)*param_3;
    if (puVar1 == (undefined8 *)0x0) {
      puVar4 = (undefined8 *)0x0;
    }
    else {
      cVar2 = (**(code **)*puVar1)(puVar1,0x20f64c9a);
      puVar4 = (undefined8 *)0x0;
      if (cVar2 != '\0') {
        puVar4 = puVar1;
      }
    }
  }
  else {
    puVar4 = (undefined8 *)CONCAT44(uStackX_1c,local_res18);
  }
  if (*(char *)(param_2 + 0x3f0) == '\0') {
    iVar3 = FUN_140406320(puVar4);
    FUN_14002f570(param_1,(double)iVar3 / DAT_1421b9278);
    return param_1;
  }
  local_res18 = (float)FUN_140406050();
  FUN_14002f570(param_1,(double)local_res18);
  return param_1;
}

