
undefined8 * FUN_1409254d0(longlong param_1,undefined8 *param_2,undefined4 param_3)

{
  longlong *plVar1;
  char cVar2;
  undefined8 *puVar3;
  undefined8 *puVar4;
  undefined8 *local_res8;
  
  plVar1 = *(longlong **)(*(longlong *)(param_1 + 0x20) + 8);
  if ((plVar1 == (longlong *)0x0) ||
     (cVar2 = (**(code **)(*plVar1 + 0x170))(plVar1,param_3), cVar2 == '\0')) {
    puVar4 = (undefined8 *)0x0;
  }
  else {
    puVar4 = (undefined8 *)0x0;
    plVar1 = *(longlong **)(*(longlong *)(param_1 + 0x20) + 8);
    puVar3 = puVar4;
    if (plVar1 != (longlong *)0x0) {
      local_res8 = (undefined8 *)0x0;
      (**(code **)(*plVar1 + 0x110))(plVar1,param_3,&local_res8);
      puVar3 = local_res8;
    }
    cVar2 = FUN_140052590(param_2,puVar3);
    if (cVar2 != '\0') {
      return param_2;
    }
    if ((puVar3 != (undefined8 *)0x0) &&
       (cVar2 = (**(code **)*puVar3)(puVar3,0xc1e758f), cVar2 != '\0')) {
      puVar4 = puVar3;
    }
  }
  *param_2 = puVar4;
  return param_2;
}

