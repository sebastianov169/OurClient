
undefined8 * FUN_140924900(undefined8 *param_1,longlong *param_2)

{
  longlong lVar1;
  uint uVar2;
  undefined4 uVar3;
  longlong *plVar4;
  undefined8 *puVar5;
  undefined8 *puVar6;
  undefined8 *puVar7;
  undefined8 local_res8;
  
  if ((int)(DWORD)DAT_1421bb758 < 0x40) {
    plVar4 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
  }
  else {
    plVar4 = TlsGetValue((DWORD)DAT_1421bb758);
  }
  puVar5 = (undefined8 *)plVar4[1];
  if ((ulonglong)plVar4[2] < (longlong)puVar5 + 0x4cU) {
    puVar5 = (undefined8 *)(**(code **)(*plVar4 + 8))(plVar4,0x48,0x800000);
  }
  else {
    plVar4[1] = (longlong)puVar5 + 0x4cU;
    *(undefined4 *)((longlong)puVar5 + -4) = 0x800048;
  }
  (**(code **)(*plVar4 + 0x18))(plVar4,puVar5,0,1);
  puVar7 = (undefined8 *)0x0;
  puVar6 = puVar7;
  if (puVar5 != (undefined8 *)0x0) {
    *puVar5 = fkengine::game::Grid_obj::vftable;
    puVar5[2] = 0;
    puVar5[3] = 0;
    puVar5[4] = 0;
    puVar5[5] = 0;
    puVar5[6] = 0;
    puVar5[7] = 0;
    puVar6 = puVar5;
  }
  lVar1 = *param_2;
  if (*(int *)(lVar1 + 0x10) < 3) {
    if (*(int *)(lVar1 + 0x14) < 3) {
      FUN_140036510(lVar1,3);
    }
    *(undefined4 *)(lVar1 + 0x10) = 3;
  }
  plVar4 = *(longlong **)(*(longlong *)(lVar1 + 0x18) + 0x10);
  if (plVar4 != (longlong *)0x0) {
    uVar2 = (**(code **)(*plVar4 + 0x38))();
    puVar7 = (undefined8 *)(ulonglong)uVar2;
  }
  lVar1 = *param_2;
  if (*(int *)(lVar1 + 0x10) < 2) {
    if (*(int *)(lVar1 + 0x14) < 2) {
      FUN_140036510(lVar1,2);
    }
    *(undefined4 *)(lVar1 + 0x10) = 2;
  }
  plVar4 = *(longlong **)(*(longlong *)(lVar1 + 0x18) + 8);
  if (plVar4 == (longlong *)0x0) {
    uVar3 = 0;
  }
  else {
    uVar3 = (**(code **)(*plVar4 + 0x38))();
  }
  lVar1 = *param_2;
  if (*(int *)(lVar1 + 0x10) < 1) {
    if (*(int *)(lVar1 + 0x14) < 1) {
      FUN_140036510(lVar1,1);
    }
    *(undefined4 *)(lVar1 + 0x10) = 1;
  }
  local_res8 = 0;
  FUN_14004fc60(&local_res8,*(undefined8 *)(lVar1 + 0x18));
  FUN_140924140(puVar6,&local_res8,uVar3,puVar7);
  *param_1 = puVar6;
  return param_1;
}

