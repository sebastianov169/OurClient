
undefined8 * FUN_14097ca60(undefined8 *param_1,longlong param_2,longlong *param_3)

{
  undefined8 *puVar1;
  longlong *plVar2;
  char cVar3;
  longlong lVar4;
  undefined8 *puVar5;
  undefined8 *local_res18;
  undefined1 local_res20 [8];
  longlong local_18 [2];
  
  cVar3 = FUN_140052590(&local_res18,*param_3);
  puVar5 = local_res18;
  if (cVar3 == '\0') {
    puVar1 = (undefined8 *)*param_3;
    if (puVar1 == (undefined8 *)0x0) {
      puVar5 = (undefined8 *)0x0;
    }
    else {
      cVar3 = (**(code **)*puVar1)(puVar1,0x64ebab04);
      puVar5 = (undefined8 *)0x0;
      if (cVar3 != '\0') {
        puVar5 = puVar1;
      }
    }
  }
  cVar3 = FUN_140052590(&local_res18,puVar5[4]);
  if (cVar3 == '\0') {
    puVar5 = (undefined8 *)puVar5[4];
    if (puVar5 == (undefined8 *)0x0) {
      local_res18 = (undefined8 *)0x0;
    }
    else {
      cVar3 = (**(code **)*puVar5)(puVar5,0x3c209fa0);
      local_res18 = (undefined8 *)0x0;
      if (cVar3 != '\0') {
        local_res18 = puVar5;
      }
    }
  }
  cVar3 = FUN_1400fd950(&local_res18,param_2 + 0x98);
  if ((cVar3 != '\0') && (*(char *)(*(longlong *)(param_2 + 0x98) + 0x38) != '\0')) {
    FUN_140b86ef0(&local_res18);
    local_res20[0] = 1;
    lVar4 = *(longlong *)(*(longlong *)(param_2 + 0x98) + 0x58);
    *(int *)(local_res18 + 10) =
         *(int *)(local_res18 + 10) + (*(int *)(lVar4 + 8) - *(int *)(lVar4 + 0x1c));
    local_18[0] = *(longlong *)(param_2 + 0x10);
    local_res18 = (undefined8 *)
                  (CONCAT44(*(undefined4 *)(local_18[0] + 8),(int)local_res18) & 0xffffffffffffff00)
    ;
    FUN_14016faf0(*(undefined8 *)(param_2 + 0x98),local_18,&local_res18,local_res20);
    if (*(int *)(param_2 + 0xac) != 0) {
      *(int *)(param_2 + 0x78) =
           *(int *)(param_2 + 0x78) + *(int *)(*(longlong *)(param_2 + 0x10) + 8);
    }
    cVar3 = FUN_140977a40(param_2);
    plVar2 = *(longlong **)(param_2 + 0x50);
    if ((plVar2 != (longlong *)0x0) && (cVar3 != '\0')) {
      lVar4 = (**(code **)(*plVar2 + 0x70))(plVar2,0xfd5399ed);
      (**(code **)(lVar4 + 0x18))(plVar2);
    }
  }
  *param_1 = 0;
  return param_1;
}

