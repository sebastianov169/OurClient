
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_140970050(longlong param_1,undefined8 *param_2)

{
  undefined4 uVar1;
  byte bVar2;
  longlong *plVar3;
  undefined8 *puVar4;
  undefined8 *puVar5;
  LPVOID pvVar6;
  longlong lVar7;
  byte *pbVar8;
  longlong lVar9;
  uint uVar10;
  undefined8 uVar11;
  double dVar12;
  undefined1 local_res8;
  byte local_res9;
  longlong local_res18;
  undefined1 local_res20 [4];
  int local_res24;
  undefined8 local_c8;
  undefined1 local_c0 [8];
  undefined8 *local_b8;
  undefined8 local_b0;
  undefined1 local_a8 [8];
  longlong local_a0;
  longlong local_98;
  longlong local_90;
  longlong local_88;
  longlong local_80;
  undefined1 local_78 [8];
  undefined1 local_70 [8];
  undefined8 local_68;
  undefined1 local_60 [8];
  undefined1 local_58 [8];
  longlong local_50;
  longlong local_48;
  undefined1 local_40 [8];
  
  if ((int)(DWORD)DAT_1421bb758 < 0x40) {
    plVar3 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
  }
  else {
    plVar3 = TlsGetValue((DWORD)DAT_1421bb758);
  }
  if (*(char *)(param_1 + 0xd8) == '\0') {
    if (*(char *)(*(longlong *)(param_1 + 0x98) + 0x38) == '\0') {
      local_c8 = 0;
      FUN_140030210(local_c0,"disconnected",param_1,FUN_140966390);
      FUN_140ffd250(local_c0,0,&local_c8);
      return;
    }
    puVar4 = (undefined8 *)plVar3[1];
    if ((ulonglong)plVar3[2] < (longlong)puVar4 + 0x1cU) {
      puVar4 = (undefined8 *)(**(code **)(*plVar3 + 8))(plVar3,0x18,0x800000);
    }
    else {
      plVar3[1] = (longlong)puVar4 + 0x1cU;
      *(undefined4 *)((longlong)puVar4 + -4) = 0x800018;
    }
    (**(code **)(*plVar3 + 0x18))(plVar3,puVar4,0,1);
    *puVar4 = DAT_1421ba810;
    FUN_1412f2790(puVar4);
    local_b0 = *param_2;
    local_b8 = puVar4;
    puVar5 = (undefined8 *)FUN_140ff3ad0(local_40,plVar3,&local_b8);
    FUN_140ff1eb0(*puVar5,&local_b0);
    uVar11 = FUN_1412f5a00(puVar4[2],&local_res18);
    lVar9 = 0;
    if (local_res18 != 0) {
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        pvVar6 = *(LPVOID *)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        pvVar6 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      local_a8[0] = 1;
      FUN_140407920(&local_98,pvVar6,local_a8);
      local_a0 = local_res18;
      uVar11 = FUN_1404072b0(local_98,&local_a0);
      lVar9 = local_98;
    }
    *(undefined4 *)(lVar9 + 0x1c) = 0;
    uVar10 = *(uint *)(param_1 + 0xc4);
    uVar1 = *(undefined4 *)(lVar9 + 8);
    if ((uVar10 & 1) == 0) {
      local_90 = lVar9;
      bVar2 = FUN_14093ad00(uVar11,&local_90);
      uVar10 = *(uint *)(param_1 + 0xc4);
      local_res24 = *(int *)(param_1 + 0x30);
    }
    else {
      local_res24 = *(int *)(param_1 + 0x30);
      if (local_res24 < 0) {
        dVar12 = 4294967296.0;
      }
      else {
        dVar12 = 0.0;
      }
      dVar12 = (double)FUN_141bf552c(dVar12 + (double)local_res24,0x404f800000000000);
      if ((dVar12 < -2147483647.0) || (2147483647.0 < dVar12)) {
        bVar2 = (byte)(longlong)dVar12;
      }
      else {
        bVar2 = (byte)(int)dVar12;
      }
    }
    local_res9 = (byte)(uVar10 >> 8) & 1;
    local_res8 = 0;
    local_res20[0] = 0;
    local_88 = lVar9;
    FUN_1403cf5d0(&local_80,&local_88,local_res20,&local_res8);
    FUN_140405a00(*(undefined8 *)(param_1 + 0x100));
    lVar7 = FUN_14002f450(0);
    lVar9 = *(longlong *)(param_1 + 0x100);
    if (((*(byte *)(lVar9 + -1) == _DAT_1420624b4) && (lVar7 != 0)) &&
       (*(char *)(lVar7 + -1) == '\0')) {
      *(byte *)(lVar9 + -1) = *(byte *)(lVar9 + -1) | 0x40;
      FUN_1400161d0(plVar3,lVar9);
    }
    *(longlong *)(lVar9 + 0x20) = lVar7;
    FUN_140406ce0(*(undefined8 *)(param_1 + 0x100),*(undefined4 *)(local_80 + 8));
    FUN_140406ce0(*(undefined8 *)(param_1 + 0x100),uVar1);
    lVar9 = *(longlong *)(param_1 + 0x100);
    FUN_1404073c0(lVar9,*(int *)(lVar9 + 0x1c) + 1);
    *(int *)(lVar9 + 0x1c) = *(int *)(lVar9 + 0x1c) + 1;
    pbVar8 = (byte *)FUN_1400281e0(*(undefined8 *)(lVar9 + 0x10));
    local_78[0] = 1;
    local_70[0] = 1;
    *pbVar8 = bVar2 & 0x3f;
    local_68 = *(undefined8 *)(param_1 + 0x100);
    FUN_140170af0(*(undefined8 *)(param_1 + 0x98),&local_68,local_70,local_78);
    local_60[0] = 1;
    local_58[0] = 1;
    local_50 = local_80;
    FUN_140170af0(*(undefined8 *)(param_1 + 0x98),&local_50,local_58,local_60);
    FUN_14016f690(*(undefined8 *)(param_1 + 0x98));
    FUN_140b86ef0(&local_48);
    *(int *)(local_48 + 0x54) =
         *(int *)(local_48 + 0x54) +
         *(int *)(*(longlong *)(param_1 + 0x100) + 8) + *(int *)(local_80 + 8);
  }
  return;
}

