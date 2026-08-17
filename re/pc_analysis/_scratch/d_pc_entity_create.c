
longlong * FUN_14067e6e0(longlong *param_1,longlong *param_2)

{
  undefined8 *puVar1;
  char cVar2;
  undefined8 *puVar3;
  
  cVar2 = FUN_140052590(param_1,*param_2);
  if (cVar2 == '\0') {
    puVar1 = (undefined8 *)*param_2;
    if (puVar1 != (undefined8 *)0x0) {
      cVar2 = (**(code **)*puVar1)(puVar1,0xc1e758f);
      puVar3 = (undefined8 *)0x0;
      if (cVar2 != '\0') {
        puVar3 = puVar1;
      }
      *param_1 = (longlong)puVar3;
      return param_1;
    }
    *param_1 = 0;
  }
  return param_1;
}

