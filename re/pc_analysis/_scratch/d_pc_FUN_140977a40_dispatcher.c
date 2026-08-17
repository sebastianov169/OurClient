
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

ulonglong FUN_140977a40(longlong param_1)

{
  undefined8 uVar1;
  char cVar2;
  int iVar3;
  uint uVar4;
  undefined4 uVar5;
  LPVOID pvVar6;
  longlong lVar7;
  undefined8 *puVar8;
  longlong *plVar9;
  longlong *plVar10;
  ulonglong uVar11;
  int iVar12;
  longlong *plVar13;
  ulonglong uVar14;
  double dVar15;
  undefined8 uVar16;
  undefined8 extraout_XMM0_Qa;
  undefined8 extraout_XMM0_Qa_00;
  undefined1 local_res10;
  byte local_res11;
  undefined1 local_res18 [4];
  undefined4 local_res1c;
  undefined1 local_res20 [4];
  int local_res24;
  undefined1 local_1f8 [4];
  undefined4 local_1f4;
  undefined1 local_1f0 [4];
  undefined4 local_1ec;
  undefined8 local_1e8;
  undefined8 local_1e0;
  longlong local_1d8;
  undefined1 local_1d0 [8];
  undefined1 local_1c8 [8];
  longlong local_1c0;
  undefined8 local_1b8;
  undefined8 local_1b0;
  longlong local_1a8;
  undefined8 local_1a0;
  undefined8 local_198;
  undefined8 local_190;
  undefined1 local_188 [8];
  undefined8 local_180;
  longlong local_178;
  longlong *local_170;
  undefined8 local_168;
  longlong *local_160;
  undefined8 local_158;
  longlong local_150 [4];
  undefined1 local_130 [8];
  longlong local_128;
  undefined8 local_110;
  undefined1 local_108 [8];
  undefined1 local_100 [8];
  undefined1 local_f8 [8];
  undefined1 local_f0 [24];
  undefined1 local_d8 [16];
  undefined1 local_c8 [16];
  undefined1 local_b8 [128];
  
  local_110 = 0xfffffffffffffffe;
  if ((int)(DWORD)DAT_1421bb758 < 0x40) {
    pvVar6 = *(LPVOID *)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
  }
  else {
    pvVar6 = TlsGetValue((DWORD)DAT_1421bb758);
  }
  uVar11 = 0;
  plVar13 = local_170;
  do {
    while( true ) {
      if (*(char *)(param_1 + 0x7c) != '\x01') {
        return uVar11;
      }
      iVar3 = *(int *)(param_1 + 0x28);
      if (iVar3 == -1) {
        lVar7 = *(longlong *)(param_1 + 0x10);
        if (2 < *(int *)(lVar7 + 8)) {
          iVar3 = FUN_140406270(lVar7);
          uVar4 = FUN_140406270(lVar7);
          if ((*(longlong **)(lVar7 + 0x20) == (longlong *)0x0) ||
             (dVar15 = (double)(**(code **)(**(longlong **)(lVar7 + 0x20) + 0x40))(), dVar15 != 1.0)
             ) {
            uVar4 = uVar4 | iVar3 << 8;
          }
          else {
            uVar4 = uVar4 * 0x100 + iVar3;
          }
          *(uint *)(param_1 + 0x28) = uVar4;
          if (uVar4 == 0xffff) {
            iVar3 = FUN_140406050(*(undefined8 *)(param_1 + 0x10));
            *(int *)(param_1 + 0x28) = iVar3 + 0xffff;
          }
          iVar3 = FUN_140406270(*(undefined8 *)(param_1 + 0x10));
          if ((char)iVar3 < '\0') {
            iVar3 = iVar3 + -0x100;
          }
          *(bool *)(param_1 + 0x2c) = iVar3 == 1;
          *(bool *)(param_1 + 0x2d) = iVar3 == 2;
          iVar3 = *(int *)(param_1 + 0x28);
        }
        if (iVar3 == -1) {
          return uVar11;
        }
      }
      dVar15 = (double)(*(int *)(*(longlong *)(param_1 + 0x10) + 8) -
                       *(int *)(*(longlong *)(param_1 + 0x10) + 0x1c));
      if ((dVar15 < -2147483647.0) || (2147483647.0 < dVar15)) {
        iVar12 = (int)(longlong)dVar15;
      }
      else {
        iVar12 = (int)dVar15;
      }
      dVar15 = (double)iVar3;
      if ((dVar15 < -2147483647.0) || (2147483647.0 < dVar15)) {
        iVar3 = (int)(longlong)dVar15;
      }
      else {
        iVar3 = (int)dVar15;
      }
      if (iVar12 < iVar3) {
        return uVar11;
      }
      lVar7 = *(longlong *)(param_1 + 0x18);
      FUN_140036a90(*(undefined8 *)(lVar7 + 0x10),0);
      *(undefined4 *)(lVar7 + 0x28) = 0;
      *(undefined4 *)(lVar7 + 8) = 0;
      *(undefined4 *)(lVar7 + 0x1c) = 0;
      uVar16 = *(undefined8 *)(param_1 + 0x10);
      uVar1 = *(undefined8 *)(param_1 + 0x18);
      uVar4 = FUN_140231780(0x1201,0x31);
      uVar14 = (ulonglong)uVar4;
      iVar3 = FUN_140232fe0();
      FUN_140231a80(0x1201,uVar14 & 0xffffffff,0x32);
      local_res24 = iVar3 + -100;
      local_res18[0] = 0;
      local_res1c = *(undefined4 *)(param_1 + 0x28);
      local_res20[0] = 0;
      local_1e0 = uVar1;
      FUN_140405dd0(uVar16,&local_1e0,local_res20,local_res18);
      local_1f8[0] = 0;
      plVar10 = (longlong *)0x0;
      local_1f4 = 0;
      FUN_140407920(&local_1d8,pvVar6,local_1f8);
      lVar7 = local_1d8;
      local_1d0[0] = 1;
      local_1c8[0] = 1;
      local_1c0 = local_1d8;
      FUN_140405dd0(*(undefined8 *)(param_1 + 0x10),&local_1c0,local_1c8,local_1d0);
      if (((*(byte *)(param_1 + -1) == _DAT_1420624b4) && (lVar7 != 0)) &&
         (*(char *)(lVar7 + -1) == '\0')) {
        *(byte *)(param_1 + -1) = *(byte *)(param_1 + -1) | 0x40;
        FUN_1400161d0(pvVar6,param_1);
      }
      *(longlong *)(param_1 + 0x10) = lVar7;
      *(undefined4 *)(lVar7 + 0x1c) = 0;
      *(undefined4 *)(param_1 + 0x28) = 0xffffffff;
      if (*(char *)(param_1 + 0x2c) == '\0') break;
      uVar11 = 1;
      *(undefined4 *)(*(longlong *)(param_1 + 0x18) + 0x1c) = 0;
      plVar10 = *(longlong **)(param_1 + 0x50);
      if (plVar10 != (longlong *)0x0) {
        DAT_1420624bc = 0;
        local_1b8 = *(undefined8 *)(param_1 + 0x18);
        lVar7 = (**(code **)(*plVar10 + 0x70))(plVar10,0xfd5399ed);
        (**(code **)(lVar7 + 8))(plVar10,&local_1b8);
        DAT_1420624bc = 1;
      }
    }
    local_res11 = (byte)((uint)*(undefined4 *)(param_1 + 0xc4) >> 8) & 1;
    local_res10 = 0;
    local_1b0 = 0;
    local_1f0[0] = 0;
    local_1ec = *(undefined4 *)(param_1 + 0x30);
    local_1a8 = *(longlong *)(param_1 + 0x18);
    FUN_1403cf030(&local_1e8,&local_1a8,local_1f0,&local_1b0,&local_res10);
    if (*(char *)(param_1 + 0x2d) != '\0') {
      local_1a0 = FUN_14002f450(0);
      FUN_1404066c0(local_1e8,&local_1a0);
    }
    local_198 = 0;
    local_190 = 0;
    puVar8 = (undefined8 *)FUN_1412f4da0(local_108,pvVar6,local_188,&local_190,&local_198);
    local_180 = *puVar8;
    plVar9 = (longlong *)FUN_14183ba50(local_100,pvVar6,&local_180);
    lVar7 = *plVar9;
    uVar5 = (**(code **)(**(longlong **)(lVar7 + 0x28) + 0x100))();
    uVar16 = FUN_141839810(lVar7,&local_178,uVar5);
    lVar7 = local_178;
    plVar9 = DAT_1421bb790;
    if (local_178 != 0) {
      if (DAT_1421bb790 == DAT_1421bc000) goto LAB_140977ee4;
      cVar2 = FUN_140052590(&local_170,DAT_1421bb790);
      if (cVar2 == '\0') {
        plVar13 = plVar10;
        if (plVar9 == (longlong *)0x0) goto LAB_140977eb4;
        cVar2 = (**(code **)*plVar9)(plVar9,2);
        if (cVar2 != '\0') {
          plVar13 = plVar9;
        }
      }
      if (plVar13 != (longlong *)0x0) {
        if ((code *)plVar13[1] == (code *)0x0) {
          cVar2 = (**(code **)(*plVar13 + 0x118))(plVar13,lVar7);
          uVar16 = extraout_XMM0_Qa_00;
        }
        else {
          cVar2 = (*(code *)plVar13[1])(lVar7);
          uVar16 = extraout_XMM0_Qa;
        }
        if (cVar2 != '\0') {
LAB_140977ee4:
          uVar16 = FUN_14097c0d0(uVar16,local_d8);
          uVar16 = FUN_14097b770(uVar16,local_c8);
          FUN_14097ae10(uVar16,local_b8);
          puVar8 = (undefined8 *)FUN_140050a60(local_f8,local_b8,0x698,local_c8,local_d8);
          local_168 = *puVar8;
          FUN_14097a520(local_168,local_130);
          if (local_128 != 0) {
            plVar10 = (longlong *)FUN_140055a30(local_130);
          }
          local_160 = plVar10;
          if (DAT_1421c0808 != (longlong *)0x0) {
            uVar11 = (**(code **)(*DAT_1421c0808 + 0xe0))
                               (DAT_1421c0808,local_f0,&local_160,&local_168);
            if ((*(longlong *)(param_1 + 0x20) != 0) || (*(longlong *)(param_1 + 0x50) != 0)) {
              local_158 = 0;
              uVar11 = FUN_1409336f0(param_1,&local_158);
            }
            return uVar11 & 0xffffffffffffff00;
          }
                    /* WARNING: Subroutine does not return */
          FUN_14002fb60();
        }
      }
    }
LAB_140977eb4:
    local_150[0] = lVar7;
    FUN_140945f80(param_1,local_150);
  } while( true );
}

