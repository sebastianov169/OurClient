
undefined8 * FUN_1409662f0(undefined8 *param_1,longlong param_2,longlong *param_3)

{
  undefined8 *puVar1;
  longlong *plVar2;
  char cVar3;
  longlong lVar4;
  undefined8 *local_res18 [2];
  
  cVar3 = FUN_140052590(local_res18,*param_3);
  if (cVar3 == '\0') {
    puVar1 = (undefined8 *)*param_3;
    if (puVar1 == (undefined8 *)0x0) {
      local_res18[0] = (undefined8 *)0x0;
    }
    else {
      cVar3 = (**(code **)*puVar1)(puVar1,0x20f64c9a);
      local_res18[0] = (undefined8 *)0x0;
      if (cVar3 != '\0') {
        local_res18[0] = puVar1;
      }
    }
  }
  plVar2 = *(longlong **)(param_2 + 0x50);
  if (plVar2 != (longlong *)0x0) {
    DAT_1420624bc = 0;
    lVar4 = (**(code **)(*plVar2 + 0x70))(plVar2,0xfd5399ed);
    (**(code **)(lVar4 + 8))(plVar2,local_res18);
    DAT_1420624bc = 1;
  }
  *param_1 = 0;
  return param_1;
}

