
void FUN_14073b220(longlong param_1,undefined8 *param_2)

{
  char cVar1;
  undefined1 uVar2;
  undefined4 uVar3;
  undefined4 uVar4;
  int iVar5;
  LPVOID pvVar6;
  longlong *plVar7;
  undefined8 uVar8;
  undefined8 *puVar9;
  undefined8 uVar10;
  undefined8 uVar11;
  longlong *plVar12;
  longlong lVar13;
  double dVar14;
  undefined8 extraout_XMM0_Qa;
  undefined8 extraout_XMM0_Qa_00;
  undefined8 extraout_XMM0_Qa_01;
  undefined1 local_res8 [8];
  undefined4 local_res18 [2];
  undefined4 local_res20 [2];
  undefined4 local_2b8;
  undefined4 local_2b4;
  undefined4 local_2b0;
  undefined4 local_2ac;
  undefined4 local_2a8;
  undefined4 local_2a4;
  undefined4 local_2a0;
  undefined4 local_29c;
  undefined4 local_298;
  undefined4 local_294;
  undefined4 local_290;
  undefined4 local_28c;
  undefined4 local_288 [2];
  longlong local_280;
  longlong local_278;
  undefined8 local_270;
  undefined8 local_268;
  longlong local_260;
  longlong local_258;
  undefined8 local_250;
  longlong local_248;
  longlong local_240;
  longlong local_238;
  longlong *local_230;
  longlong *local_228;
  longlong local_220;
  undefined8 local_218;
  undefined4 local_210 [2];
  undefined4 local_208;
  undefined1 local_200 [8];
  undefined4 local_1f8;
  undefined4 local_1f0 [2];
  undefined4 local_1e8;
  undefined1 local_1e0 [8];
  undefined1 local_1d8 [8];
  undefined1 local_1d0 [8];
  undefined1 local_1c8 [8];
  undefined1 local_1c0 [8];
  undefined1 local_1b8 [8];
  undefined1 local_1b0 [8];
  undefined1 local_1a8 [8];
  undefined1 local_1a0 [8];
  undefined1 local_198 [8];
  undefined1 local_190 [8];
  undefined1 local_188 [8];
  undefined1 local_180 [8];
  undefined1 local_178 [8];
  undefined1 local_170 [8];
  undefined1 local_168 [8];
  undefined1 local_160 [8];
  undefined1 local_158 [8];
  undefined1 local_150 [8];
  undefined1 local_148 [8];
  undefined1 local_140 [8];
  undefined1 local_138 [8];
  undefined1 local_130 [8];
  undefined1 local_128 [8];
  undefined1 local_120 [8];
  undefined1 local_118 [8];
  undefined1 local_110 [8];
  undefined1 local_108 [8];
  undefined1 local_100 [8];
  undefined1 local_f8 [8];
  undefined1 local_f0 [8];
  undefined1 local_e8 [8];
  undefined1 local_e0 [8];
  undefined1 local_d8 [8];
  undefined1 local_d0 [8];
  undefined1 local_c8 [8];
  undefined1 local_c0 [8];
  undefined1 local_b8 [8];
  undefined1 local_b0 [8];
  undefined1 local_a8 [8];
  undefined1 local_a0 [16];
  undefined1 local_90 [16];
  undefined1 local_80 [16];
  undefined1 local_70 [16];
  undefined1 local_60 [16];
  undefined1 local_50 [24];
  
  if ((int)(DWORD)DAT_1421bb758 < 0x40) {
    pvVar6 = *(LPVOID *)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
  }
  else {
    pvVar6 = TlsGetValue((DWORD)DAT_1421bb758);
  }
  if (*(char *)(param_1 + 0x432) == '\0') {
    local_280 = param_1;
    local_278 = param_1;
    FUN_1404666a0(DAT_1421b87a4,&local_278,&local_280);
    *(undefined1 *)(param_1 + 0x432) = 1;
  }
  plVar7 = (longlong *)(**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_b8,2);
  if ((longlong *)*plVar7 == (longlong *)0x0) {
    uVar3 = 0;
  }
  else {
    uVar3 = (**(code **)(*(longlong *)*plVar7 + 0x38))();
  }
  plVar7 = (longlong *)FUN_1409254d0(*(undefined8 *)(param_1 + 0x308),local_b0,uVar3);
  if (*plVar7 != 0) {
    return;
  }
  plVar7 = (longlong *)(**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_a8,3);
  if (((longlong *)*plVar7 == (longlong *)0x0) ||
     (dVar14 = (double)(**(code **)(*(longlong *)*plVar7 + 0x40))(), uVar10 = DAT_1421cc3a0,
     dVar14 != 14.0)) {
    plVar7 = (longlong *)
             (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_1e0,0);
    if (((longlong *)*plVar7 == (longlong *)0x0) ||
       (dVar14 = (double)(**(code **)(*(longlong *)*plVar7 + 0x40))(), uVar10 = DAT_1421cc3a0,
       dVar14 != 11.0)) {
      plVar7 = (longlong *)
               (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_1d8,0);
      if (((longlong *)*plVar7 == (longlong *)0x0) ||
         (dVar14 = (double)(**(code **)(*(longlong *)*plVar7 + 0x40))(), uVar10 = DAT_1421cc3a8,
         dVar14 != 5.0)) {
        plVar7 = (longlong *)
                 (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_1d0,3);
        if (((longlong *)*plVar7 == (longlong *)0x0) ||
           (dVar14 = (double)(**(code **)(*(longlong *)*plVar7 + 0x40))(), uVar10 = DAT_1421cc3a8,
           dVar14 != 5.0)) {
          local_res18[0] = 7;
          uVar10 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_1c8,0);
          cVar1 = FUN_1400d01d0(uVar10,local_res18);
          uVar10 = DAT_1421cc3b0;
          if (cVar1 != '\0') {
            local_res20[0] = 7;
            uVar10 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_1c0,3);
            cVar1 = FUN_1401181c0(uVar10,local_res20);
            uVar10 = DAT_1421cc3b0;
            if (cVar1 == '\0') {
              local_2b8 = 9;
              uVar10 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_1b8,3)
              ;
              cVar1 = FUN_1400d01d0(uVar10,&local_2b8);
              uVar10 = DAT_1421c16f8;
              if (cVar1 != '\0') {
                local_2b4 = 9;
                uVar10 = (**(code **)(*(longlong *)*param_2 + 0xb8))
                                   ((longlong *)*param_2,local_1b0,0);
                cVar1 = FUN_1401181c0(uVar10,&local_2b4);
                uVar10 = DAT_1421c16f8;
                if (cVar1 == '\0') {
                  local_2b0 = 8;
                  uVar10 = (**(code **)(*(longlong *)*param_2 + 0xb8))
                                     ((longlong *)*param_2,local_1a8,0);
                  cVar1 = FUN_1401181c0(uVar10,&local_2b0);
                  uVar10 = DAT_1421c1728;
                  if (cVar1 == '\0') {
                    local_2ac = 1;
                    uVar10 = (**(code **)(*(longlong *)*param_2 + 0xb8))
                                       ((longlong *)*param_2,local_1a0,0);
                    cVar1 = FUN_1401181c0(uVar10,&local_2ac);
                    uVar10 = 0;
                    if (cVar1 != '\0') {
                      uVar10 = DAT_1421c1718;
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
  local_2a8 = 0xd;
  uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_198,0);
  cVar1 = FUN_1401181c0(uVar8,&local_2a8);
  local_2a4 = 0xe;
  if (cVar1 != '\0') {
    uVar10 = DAT_1421c16d8;
  }
  uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_190,0);
  cVar1 = FUN_1401181c0(uVar8,&local_2a4);
  local_2a0 = 2;
  if (cVar1 != '\0') {
    uVar10 = DAT_1421c16e8;
  }
  uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_188,0);
  cVar1 = FUN_1401181c0(uVar8,&local_2a0);
  local_29c = 4;
  if (cVar1 != '\0') {
    uVar10 = DAT_1421c16f0;
  }
  uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_180,0);
  cVar1 = FUN_1401181c0(uVar8,&local_29c);
  local_298 = 3;
  if (cVar1 != '\0') {
    uVar10 = DAT_1421c16b0;
  }
  uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_178,0);
  cVar1 = FUN_1401181c0(uVar8,&local_298);
  local_294 = 6;
  if (cVar1 != '\0') {
    uVar10 = DAT_1421cc388;
  }
  uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_170,0);
  cVar1 = FUN_1401181c0(uVar8,&local_294);
  local_290 = 0xc;
  if (cVar1 != '\0') {
    uVar10 = DAT_1421cc390;
  }
  uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_168,0);
  cVar1 = FUN_1401181c0(uVar8,&local_290);
  local_28c = 0xf;
  if (cVar1 != '\0') {
    uVar10 = DAT_1421c1730;
  }
  uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_160,0);
  cVar1 = FUN_1401181c0(uVar8,&local_28c);
  if (cVar1 != '\0') {
    uVar10 = DAT_1421c16c8;
  }
  local_270 = uVar10;
  FUN_14073bbe0(extraout_XMM0_Qa,local_a0);
  cVar1 = FUN_140b79010(local_a0);
  if (((cVar1 != '\0') && (cVar1 = FUN_1400fd950(&local_270,&DAT_1421c1718), cVar1 != '\0')) &&
     (0 < *(int *)(DAT_1421c1700 + 0x10))) {
    local_288[0] = 0xb;
    uVar8 = (**(code **)(*(longlong *)*param_2 + 0xb8))((longlong *)*param_2,local_158,5);
    cVar1 = FUN_1401181c0(uVar8,local_288);
    if (cVar1 != '\0') {
      puVar9 = (undefined8 *)FUN_140028670(DAT_1421c1700,local_150);
      plVar7 = (longlong *)*param_2;
      plVar12 = (longlong *)*puVar9;
      uVar8 = (**(code **)(*plVar7 + 0xb8))(plVar7,local_148,2);
      uVar3 = FUN_1400219d0(uVar8);
      uVar8 = (**(code **)(*plVar7 + 0xb8))(plVar7,local_140,1);
      uVar4 = FUN_1400219d0(uVar8);
      cVar1 = FUN_1406773d0(plVar12,uVar4,uVar3);
      if (cVar1 != '\0') {
        lVar13 = *plVar12;
        uVar10 = FUN_14004fd90(local_138,param_2);
        (**(code **)(lVar13 + 0x150))(plVar12,uVar10);
        goto LAB_14073baec;
      }
    }
  }
  plVar7 = (longlong *)*param_2;
  puVar9 = (undefined8 *)FUN_140021ce0(local_130,2);
  uVar8 = *puVar9;
  uVar11 = (**(code **)(*plVar7 + 0xb8))(plVar7,local_128,1);
  puVar9 = (undefined8 *)FUN_1400b9af0(uVar8,local_120,0,uVar11);
  uVar8 = *puVar9;
  local_268 = uVar10;
  uVar10 = (**(code **)(*plVar7 + 0xb8))(plVar7,local_118,2);
  uVar10 = FUN_1400b9af0(uVar8,local_110,1,uVar10);
  uVar10 = FUN_14183d390(local_108,&local_268,uVar10);
  puVar9 = (undefined8 *)FUN_14067e6e0(local_100,uVar10);
  plVar12 = (longlong *)*puVar9;
  lVar13 = *plVar12;
  uVar10 = FUN_14004fd90(local_f8,param_2);
  (**(code **)(lVar13 + 0x150))(plVar12,uVar10);
  local_260 = plVar12[0xb];
  uVar10 = *(undefined8 *)(DAT_1421c17a8 + 0x2b8);
  uVar3 = (**(code **)(*plVar12 + 0x220))(plVar12);
  puVar9 = (undefined8 *)FUN_1413204a0(uVar10,local_f0,uVar3);
  FUN_141320d50(*puVar9,&local_260);
  if (plVar12[0xc] != 0) {
    uVar10 = *(undefined8 *)(DAT_1421c17a8 + 0x2b8);
    local_258 = plVar12[0xc];
    uVar3 = (**(code **)(*plVar12 + 0x220))(plVar12);
    puVar9 = (undefined8 *)FUN_1413204a0(uVar10,local_e8,uVar3);
    FUN_141320d50(*puVar9,&local_258);
  }
  if ((int)plVar12[5] != 0) {
    cVar1 = FUN_1417664e0(*(undefined8 *)(param_1 + 0x358));
    if (cVar1 == '\0') {
      plVar7 = *(longlong **)(param_1 + 0x338);
      local_res8[0] = 1;
      FUN_14073c540(extraout_XMM0_Qa_00,local_90);
      uVar10 = (**(code **)(*plVar7 + 0x68))(plVar7,local_50,local_90,1);
      uVar2 = FUN_140592a30(uVar10,local_res8);
      plVar7 = (longlong *)
               FUN_14068a470(local_e0,pvVar6,(int)plVar12[5],uVar2,*(undefined1 *)(param_1 + 0x5c0),
                             *(undefined1 *)(param_1 + 0x651));
      local_1f0[0] = 0xffffffff;
      local_1e8 = 3;
      local_200[0] = 0;
      lVar13 = *plVar7;
      local_1f8 = 5;
      local_210[0] = 0xffffffff;
      local_208 = 3;
      uVar10 = FUN_14073e0a0(extraout_XMM0_Qa_01,local_60);
      uVar10 = FUN_14073d740(uVar10,local_70);
      FUN_14073ce70(uVar10,local_80);
      puVar9 = (undefined8 *)FUN_14005d860(local_d8,3);
      uVar10 = FUN_14005d940(*puVar9,0,local_80,local_210);
      uVar10 = FUN_14005d940(uVar10,1,local_70,local_200);
      local_250 = FUN_14005d940(uVar10,2,local_60,local_1f0);
      FUN_140685870(lVar13,&local_250);
      *(undefined1 *)(lVar13 + 0x7c) = 1;
      local_248 = lVar13;
      FUN_1400286d0(*(undefined8 *)(param_1 + 0x350),&local_248);
      local_240 = lVar13;
      FUN_1417663a0(*(undefined8 *)(param_1 + 0x358),*(undefined4 *)(lVar13 + 0x18),&local_240);
      if (*(longlong *)(param_1 + 0x490) != 0) {
        local_238 = lVar13;
        FUN_14133ba40(*(longlong *)(param_1 + 0x490),&local_238);
      }
    }
    else {
      uVar10 = FUN_141766420(*(undefined8 *)(param_1 + 0x358),local_d0,(int)plVar12[5]);
      plVar7 = (longlong *)FUN_1406695a0(local_c8,uVar10);
      lVar13 = *plVar7;
    }
    local_230 = plVar12;
    uVar10 = FUN_14068f760(local_c0,&local_230);
    FUN_1406874e0(lVar13,uVar10);
  }
  (**(code **)(*plVar12 + 0x170))(plVar12);
LAB_14073baec:
  local_228 = plVar12;
  FUN_140926460(*(undefined8 *)(param_1 + 0x308),&local_228);
  iVar5 = (**(code **)(*plVar12 + 0x220))(plVar12);
  if (((iVar5 == 1) || (iVar5 = (**(code **)(*plVar12 + 0x220))(plVar12), iVar5 == 0xb)) ||
     ((iVar5 = (**(code **)(*plVar12 + 0x220))(plVar12), iVar5 == 8 ||
      ((iVar5 = (**(code **)(*plVar12 + 0x220))(plVar12), iVar5 == 9 ||
       (iVar5 = (**(code **)(*plVar12 + 0x220))(plVar12), iVar5 == 10)))))) {
    uVar10 = *(undefined8 *)(param_1 + 0x2b8);
    uVar3 = (**(code **)(*plVar12 + 0x220))(plVar12);
    FUN_1413204a0(uVar10,&local_220,uVar3);
    if (*(char *)(local_220 + 0x80) != '\0') {
      local_218 = *(undefined8 *)(plVar12[0xb] + 8);
      FUN_140a229f0(*(undefined8 *)(local_220 + 8),&local_218);
    }
  }
  return;
}

