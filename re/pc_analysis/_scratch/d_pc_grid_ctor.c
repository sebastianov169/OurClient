
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_140924140(longlong param_1,longlong *param_2,int param_3,int param_4)

{
  longlong lVar1;
  longlong lVar2;
  int *piVar3;
  int *piVar4;
  int iVar5;
  LPVOID pvVar6;
  longlong *plVar7;
  undefined8 *puVar8;
  undefined8 uVar9;
  undefined8 *puVar10;
  int iVar11;
  undefined8 *puVar12;
  uint uVar13;
  bool bVar14;
  double dVar15;
  undefined8 *local_res8;
  longlong *local_res10;
  uint local_res18;
  longlong *local_148;
  longlong *local_140;
  longlong *local_138;
  longlong local_130;
  longlong local_128;
  undefined1 local_120 [8];
  undefined1 local_118 [8];
  undefined1 local_110 [8];
  undefined1 local_108 [8];
  undefined8 *local_100;
  undefined1 local_f8 [8];
  undefined8 local_f0;
  undefined1 local_e8 [8];
  undefined8 local_e0;
  undefined1 local_d8 [8];
  undefined8 local_d0;
  undefined1 local_c8 [8];
  undefined8 local_c0;
  undefined8 local_b8;
  undefined1 local_b0 [8];
  undefined1 local_a8 [8];
  longlong local_a0;
  undefined1 local_98 [8];
  longlong local_90;
  undefined1 local_88 [8];
  undefined1 local_80 [8];
  longlong local_78;
  undefined1 local_70 [8];
  longlong local_68;
  undefined1 local_60 [8];
  undefined1 local_58 [8];
  longlong local_50;
  undefined1 local_48 [8];
  undefined8 *local_40;
  
  local_b8 = 0xfffffffffffffffe;
  if ((int)(DWORD)DAT_1421bb758 < 0x40) {
    pvVar6 = *(LPVOID *)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
  }
  else {
    pvVar6 = TlsGetValue((DWORD)DAT_1421bb758);
  }
  *(undefined8 *)(param_1 + 0x40) = 0;
  local_120[0] = 1;
  local_118[0] = 1;
  local_110[0] = 1;
  local_108[0] = 1;
  plVar7 = (longlong *)FUN_141807910(local_b0,pvVar6,local_108,local_110,local_118,local_120);
  if (((*(byte *)(param_1 + -1) == _DAT_1420624b4) && (*plVar7 != 0)) &&
     (*(char *)(*plVar7 + -1) == '\0')) {
    *(byte *)(param_1 + -1) = *(byte *)(param_1 + -1) | 0x40;
    FUN_1400161d0(pvVar6,param_1);
  }
  *(longlong *)(param_1 + 0x38) = *plVar7;
  plVar7 = (longlong *)FUN_14002a350(local_a8,0,0);
  if (((*(byte *)(param_1 + -1) == _DAT_1420624b4) && (*plVar7 != 0)) &&
     (*(char *)(*plVar7 + -1) == '\0')) {
    *(byte *)(param_1 + -1) = *(byte *)(param_1 + -1) | 0x40;
    FUN_1400161d0(pvVar6,param_1);
  }
  local_a0 = *plVar7;
  *(longlong *)(param_1 + 0x30) = local_a0;
  plVar7 = (longlong *)FUN_14002a350(local_98,0,0);
  if (((*(byte *)(param_1 + -1) == _DAT_1420624b4) && (*plVar7 != 0)) &&
     (*(char *)(*plVar7 + -1) == '\0')) {
    *(byte *)(param_1 + -1) = *(byte *)(param_1 + -1) | 0x40;
    FUN_1400161d0(pvVar6,param_1);
  }
  local_90 = *plVar7;
  *(longlong *)(param_1 + 0x28) = local_90;
  plVar7 = (longlong *)FUN_141766660(local_88,pvVar6);
  if (((*(byte *)(param_1 + -1) == _DAT_1420624b4) && (*plVar7 != 0)) &&
     (*(char *)(*plVar7 + -1) == '\0')) {
    *(byte *)(param_1 + -1) = *(byte *)(param_1 + -1) | 0x40;
    FUN_1400161d0(pvVar6,param_1);
  }
  *(longlong *)(param_1 + 0x20) = *plVar7;
  *(undefined4 *)(param_1 + 0xc) = 0x200;
  *(undefined4 *)(param_1 + 8) = 0;
  plVar7 = (longlong *)FUN_14002a350(local_80,0,0);
  if (((*(byte *)(param_1 + -1) == _DAT_1420624b4) && (*plVar7 != 0)) &&
     (*(char *)(*plVar7 + -1) == '\0')) {
    *(byte *)(param_1 + -1) = *(byte *)(param_1 + -1) | 0x40;
    FUN_1400161d0(pvVar6,param_1);
  }
  local_78 = *plVar7;
  *(longlong *)(param_1 + 0x10) = local_78;
  plVar7 = (longlong *)FUN_14002a350(local_70,0,0);
  if (((*(byte *)(param_1 + -1) == _DAT_1420624b4) && (*plVar7 != 0)) &&
     (*(char *)(*plVar7 + -1) == '\0')) {
    *(byte *)(param_1 + -1) = *(byte *)(param_1 + -1) | 0x40;
    FUN_1400161d0(pvVar6,param_1);
  }
  local_68 = *plVar7;
  *(longlong *)(param_1 + 0x18) = local_68;
  *(int *)(param_1 + 8) = param_3;
  DAT_1421b931c = param_4;
  if (*(int *)(*param_2 + 0x10) == 1) {
    local_res10 = (longlong *)0x0;
  }
  else {
    plVar7 = *(longlong **)(*param_2 + 0x18);
    (**(code **)(*plVar7 + 0xb8))(plVar7,&local_res10,3);
  }
  local_f8[0] = local_res10 == (longlong *)0x0;
  if (local_res10 != (longlong *)0x0) {
    local_f0 = (**(code **)(*local_res10 + 0x40))();
  }
  if (*(int *)(*param_2 + 0x10) == 1) {
    local_148 = (longlong *)0x0;
  }
  else {
    plVar7 = *(longlong **)(*param_2 + 0x18);
    (**(code **)(*plVar7 + 0xb8))(plVar7,&local_148,2);
  }
  local_e8[0] = local_148 == (longlong *)0x0;
  if (local_148 != (longlong *)0x0) {
    local_e0 = (**(code **)(*local_148 + 0x40))();
  }
  if (*(int *)(*param_2 + 0x10) == 1) {
    local_140 = (longlong *)0x0;
  }
  else {
    plVar7 = *(longlong **)(*param_2 + 0x18);
    (**(code **)(*plVar7 + 0xb8))(plVar7,&local_140,1);
  }
  local_d8[0] = local_140 == (longlong *)0x0;
  if (local_140 != (longlong *)0x0) {
    local_d0 = (**(code **)(*local_140 + 0x40))();
  }
  if (*(int *)(*param_2 + 0x10) == 1) {
    local_138 = (longlong *)0x0;
  }
  else {
    plVar7 = *(longlong **)(*param_2 + 0x18);
    (**(code **)(*plVar7 + 0xb8))(plVar7,&local_138,0);
  }
  local_c8[0] = local_138 == (longlong *)0x0;
  if (local_138 != (longlong *)0x0) {
    local_c0 = (**(code **)(*local_138 + 0x40))();
  }
  puVar8 = (undefined8 *)FUN_140f59610(local_60,pvVar6,local_c8,local_d8,local_e8,local_f8);
  DAT_1421c2a08 = *puVar8;
  dVar15 = (double)param_3 / (double)DAT_1421b931c;
  if ((dVar15 < -2147483647.0) || (2147483647.0 < dVar15)) {
    iVar5 = (int)(longlong)dVar15;
  }
  else {
    iVar5 = (int)dVar15;
  }
  *(int *)(param_1 + 0x40) = iVar5;
  dVar15 = (double)param_3 / (double)DAT_1421b931c;
  if ((dVar15 < -2147483647.0) || (2147483647.0 < dVar15)) {
    iVar5 = (int)(longlong)dVar15;
  }
  else {
    iVar5 = (int)dVar15;
  }
  *(int *)(param_1 + 0x44) = iVar5;
  plVar7 = (longlong *)FUN_14002a350(local_58,0,0);
  if (((*(byte *)(param_1 + -1) == _DAT_1420624b4) && (*plVar7 != 0)) &&
     (*(char *)(*plVar7 + -1) == '\0')) {
    *(byte *)(param_1 + -1) = *(byte *)(param_1 + -1) | 0x40;
    FUN_1400161d0(pvVar6,param_1);
  }
  local_50 = *plVar7;
  *(longlong *)(param_1 + 0x30) = local_50;
  local_130 = (longlong)*(int *)(param_1 + 0x44);
  if (0 < local_130) {
    local_128 = -8;
    uVar13 = 0xffffffff;
    do {
      uVar13 = uVar13 + 1;
      local_128 = local_128 + 8;
      local_res18 = uVar13;
      plVar7 = (longlong *)FUN_14002a350(local_48,0,0);
      lVar1 = *plVar7;
      lVar2 = *(longlong *)(param_1 + 0x30);
      plVar7 = (longlong *)FUN_140028790(lVar2);
      if (((*(byte *)(lVar2 + -1) == _DAT_1420624b4) && (lVar1 != 0)) &&
         (*(char *)(lVar1 + -1) == '\0')) {
        *(byte *)(lVar2 + -1) = *(byte *)(lVar2 + -1) | 0x40;
        piVar3 = *(int **)((longlong)pvVar6 + 0x28);
        if (piVar3 != (int *)0x0) {
          *(longlong *)(piVar3 + (longlong)*piVar3 * 2 + 2) = lVar2;
          *piVar3 = *piVar3 + 1;
          piVar3 = *(int **)((longlong)pvVar6 + 0x28);
          if (*piVar3 == 0x80) {
            do {
              piVar4 = DAT_1421bb6c0;
              *(int **)(piVar3 + 0x102) = DAT_1421bb6c0;
              LOCK();
              bVar14 = piVar4 != DAT_1421bb6c0;
              piVar4 = piVar3;
              if (bVar14) {
                piVar4 = DAT_1421bb6c0;
              }
              DAT_1421bb6c0 = piVar4;
              UNLOCK();
            } while (bVar14);
            uVar9 = FUN_140016d70();
            *(undefined8 *)((longlong)pvVar6 + 0x28) = uVar9;
          }
        }
      }
      *plVar7 = lVar1;
      iVar11 = 0;
      iVar5 = *(int *)(param_1 + 0x40);
      if (0 < iVar5) {
        do {
          iVar11 = iVar11 + 1;
          if ((int)(DWORD)DAT_1421bb758 < 0x40) {
            plVar7 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
          }
          else {
            plVar7 = TlsGetValue((DWORD)DAT_1421bb758);
          }
          puVar8 = (undefined8 *)plVar7[1];
          if ((ulonglong)plVar7[2] < (longlong)puVar8 + 0x24U) {
            puVar8 = (undefined8 *)(**(code **)(*plVar7 + 8))(plVar7,0x20);
          }
          else {
            plVar7[1] = (longlong)puVar8 + 0x24U;
            *(undefined4 *)((longlong)puVar8 + -4) = 0x800020;
          }
          (**(code **)(*plVar7 + 0x18))(plVar7,puVar8,0,1);
          local_res8 = (undefined8 *)0x0;
          puVar12 = local_res8;
          if (puVar8 != (undefined8 *)0x0) {
            puVar8[2] = 0;
            puVar8[3] = 0;
            *(undefined4 *)(puVar8 + 1) = 0xffffffff;
            *puVar8 = Array_obj<class_Dynamic>::vftable;
            puVar12 = puVar8;
          }
          local_40 = puVar8;
          if (((uVar13 < *(uint *)(*(longlong *)(param_1 + 0x30) + 0x10)) &&
              (local_100 = *(undefined8 **)
                            (local_128 + *(longlong *)(*(longlong *)(param_1 + 0x30) + 0x18)),
              local_res8 = local_100, local_100 != (undefined8 *)0x0)) &&
             (*(int *)(local_100 + 1) != -1)) {
            local_res8 = (undefined8 *)0x0;
            FUN_140028e80(&local_res8,&local_100);
          }
          puVar8 = local_res8;
          puVar10 = (undefined8 *)FUN_140028790(local_res8);
          if (((*(byte *)((longlong)puVar8 + -1) == _DAT_1420624b4) &&
              (puVar12 != (undefined8 *)0x0)) && (*(char *)((longlong)puVar12 + -1) == '\0')) {
            *(byte *)((longlong)puVar8 + -1) = *(byte *)((longlong)puVar8 + -1) | 0x40;
            piVar3 = *(int **)((longlong)pvVar6 + 0x28);
            if (piVar3 != (int *)0x0) {
              *(undefined8 **)(piVar3 + (longlong)*piVar3 * 2 + 2) = puVar8;
              *piVar3 = *piVar3 + 1;
              piVar3 = *(int **)((longlong)pvVar6 + 0x28);
              if (*piVar3 == 0x80) {
                do {
                  piVar4 = DAT_1421bb6c0;
                  *(int **)(piVar3 + 0x102) = DAT_1421bb6c0;
                  LOCK();
                  bVar14 = piVar4 != DAT_1421bb6c0;
                  piVar4 = piVar3;
                  if (bVar14) {
                    piVar4 = DAT_1421bb6c0;
                  }
                  DAT_1421bb6c0 = piVar4;
                  UNLOCK();
                } while (bVar14);
                uVar9 = FUN_140016d70();
                *(undefined8 *)((longlong)pvVar6 + 0x28) = uVar9;
              }
            }
          }
          *puVar10 = puVar12;
          uVar13 = local_res18;
        } while (iVar11 < iVar5);
      }
      local_130 = local_130 + -1;
    } while (local_130 != 0);
  }
  return;
}

