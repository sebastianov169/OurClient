
undefined8 * FUN_140966390(undefined8 *param_1,undefined8 *param_2,longlong *param_3)

{
  undefined8 *puVar1;
  longlong *plVar2;
  char cVar3;
  longlong lVar4;
  undefined8 *puVar5;
  undefined8 *puVar6;
  undefined8 *local_res18;
  undefined8 local_res20;
  
  cVar3 = FUN_140052590(&local_res18,*param_3);
  puVar6 = (undefined8 *)0x0;
  puVar5 = local_res18;
  if (((cVar3 == '\0') &&
      (puVar1 = (undefined8 *)*param_3, puVar5 = puVar6, puVar1 != (undefined8 *)0x0)) &&
     (cVar3 = (**(code **)*puVar1)(puVar1,0x3243040d), cVar3 != '\0')) {
    puVar5 = puVar1;
  }
  if (*(char *)(param_2 + 0x36) == '\0') {
    if (*(int *)(param_2 + 0x30) != 0) {
      FUN_140ffd190();
      *(undefined4 *)(param_2 + 0x30) = 0;
    }
    if (puVar5 != (undefined8 *)0x0) {
      cVar3 = FUN_140052590(&local_res18,puVar5[4]);
      if (cVar3 == '\0') {
        puVar1 = (undefined8 *)puVar5[4];
        if (puVar1 == (undefined8 *)0x0) {
          local_res18 = (undefined8 *)0x0;
        }
        else {
          cVar3 = (**(code **)*puVar1)(puVar1,0x3c209fa0);
          local_res18 = puVar6;
          if (cVar3 != '\0') {
            local_res18 = puVar1;
          }
        }
      }
      cVar3 = FUN_1400f5d40(&local_res18,param_2 + 0x13);
      if (cVar3 != '\0') goto LAB_1409664e1;
    }
    if ((*(char *)((longlong)param_2 + 0x7c) != '\0') &&
       ((puVar5 == (undefined8 *)0x0 || (cVar3 = FUN_140966500(param_2), cVar3 == '\0')))) {
      if (*(int *)((longlong)param_2 + 0xac) != 0) {
        FUN_140ffd190();
      }
      plVar2 = (longlong *)param_2[10];
      *(undefined1 *)((longlong)param_2 + 0x7c) = 0;
      if (plVar2 == (longlong *)0x0) {
        if (param_2[4] != 0) {
          local_res18 = (undefined8 *)0x0;
          FUN_1409336f0(param_2,&local_res18);
        }
      }
      else {
        lVar4 = (**(code **)(*plVar2 + 0x70))(plVar2,0xfd5399ed);
        (**(code **)(lVar4 + 0x10))(plVar2);
      }
      local_res20 = 0;
      local_res18 = param_2;
      FUN_1404666a0(DAT_1421b871c,&local_res20,&local_res18);
    }
  }
LAB_1409664e1:
  *param_1 = 0;
  return param_1;
}

