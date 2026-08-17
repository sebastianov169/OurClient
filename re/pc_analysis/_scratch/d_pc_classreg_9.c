
void FUN_14066e0e0(void)

{
  int iVar1;
  undefined4 *puVar2;
  int *piVar3;
  uint uVar4;
  undefined8 *puVar5;
  undefined8 *puVar7;
  undefined8 *local_res8;
  undefined4 uStack_1c;
  undefined8 *puVar6;
  
  puVar2 = (undefined4 *)_malloc_base(0x8c);
  puVar6 = (undefined8 *)(puVar2 + 1);
  *puVar2 = 0x80000000;
  FUN_141bedde0(puVar6,0,0x88);
  puVar7 = (undefined8 *)0x0;
  uVar4 = 0;
  puVar5 = puVar7;
  if (puVar6 != (undefined8 *)0x0) {
    *(undefined8 *)(puVar2 + 5) = 0;
    *puVar6 = hx::Class_obj::vftable;
    puVar2[7] = 0;
    *(undefined8 *)(puVar2 + 9) = 0;
    *(undefined8 *)(puVar2 + 0xb) = 0;
    puVar2[0xd] = 0;
    *(undefined8 *)(puVar2 + 0xf) = 0;
    *(undefined8 *)(puVar2 + 0x1f) = 0;
    *(undefined8 *)(puVar2 + 0x21) = 0;
    puVar5 = puVar6;
  }
  DAT_1421c16f8 = puVar5;
  puVar5[4] = "fkengine.game.entities.ImageEntity";
  *(undefined4 *)(puVar5 + 3) = 0x22;
  DAT_1421c16f8[2] = &DAT_1421c1748;
  DAT_1421c16f8[9] = FUN_140669810;
  DAT_1421c16f8[8] = FUN_1406698d0;
  DAT_1421c16f8[0xb] = FUN_14066d300;
  DAT_1421c16f8[0xc] = FUN_14066de50;
  DAT_1421c16f8[0xd] = _guard_check_icall;
  piVar3 = &DAT_1420a5880;
  puVar6 = puVar7;
  iVar1 = DAT_1420a5880;
  while (iVar1 != 0) {
    uVar4 = (int)puVar6 + 1;
    puVar6 = (undefined8 *)(ulonglong)uVar4;
    piVar3 = piVar3 + 4;
    iVar1 = *piVar3;
  }
  puVar2 = (undefined4 *)_malloc_base(0x24);
  *puVar2 = 0x80000000;
  puVar2[1] = 0x41d32178;
  puVar2[2] = 1;
  puVar2[3] = 0xfffffffe;
  puVar2[4] = uStack_1c;
  puVar2[5] = 0;
  puVar2[6] = 0;
  puVar2[7] = 0;
  puVar2[8] = 0;
  *(int **)(puVar2 + 7) = &DAT_1420a5880;
  puVar2[5] = uVar4;
  uVar4 = 0;
  puVar2[6] = 0xffffffff;
  DAT_1421c16f8[0xf] = puVar2 + 1;
  piVar3 = &DAT_1420a5620;
  iVar1 = DAT_1420a5620;
  while (iVar1 != 0) {
    uVar4 = (int)puVar7 + 1;
    puVar7 = (undefined8 *)(ulonglong)uVar4;
    piVar3 = piVar3 + 4;
    iVar1 = *piVar3;
  }
  puVar2 = (undefined4 *)_malloc_base(0x24);
  *puVar2 = 0x80000000;
  puVar2[1] = 0x41d32178;
  puVar2[2] = 1;
  puVar2[3] = 0xfffffffe;
  puVar2[4] = uStack_1c;
  puVar2[5] = 0;
  puVar2[6] = 0;
  puVar2[7] = 0;
  puVar2[8] = 0;
  *(int **)(puVar2 + 7) = &DAT_1420a5620;
  puVar2[5] = uVar4;
  puVar2[6] = 0xffffffff;
  DAT_1421c16f8[0x10] = puVar2 + 1;
  DAT_1421c16f8[1] = FUN_14066e330;
  DAT_1421c16f8[0xe] = _guard_check_icall;
  local_res8 = DAT_1421c16f8;
  FUN_140034a30(DAT_1421c16f8 + 3,&local_res8);
  return;
}

