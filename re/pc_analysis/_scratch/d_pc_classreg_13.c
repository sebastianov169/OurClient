
void FUN_14065d9a0(void)

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
  DAT_1421c16d8 = puVar5;
  puVar5[4] = "fkengine.game.entities.SnakesPlayerEntity";
  *(undefined4 *)(puVar5 + 3) = 0x29;
  DAT_1421c16d8[2] = &DAT_1421c16f0;
  DAT_1421c16d8[9] = FUN_140659ad0;
  DAT_1421c16d8[8] = FUN_140659ba0;
  DAT_1421c16d8[0xb] = &LAB_14065cc80;
  DAT_1421c16d8[0xc] = FUN_14065d6e0;
  DAT_1421c16d8[0xd] = &LAB_14065d960;
  piVar3 = &DAT_1420a4fd0;
  puVar6 = puVar7;
  iVar1 = DAT_1420a4fd0;
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
  *(int **)(puVar2 + 7) = &DAT_1420a4fd0;
  puVar2[5] = uVar4;
  uVar4 = 0;
  puVar2[6] = 0xffffffff;
  DAT_1421c16d8[0xf] = puVar2 + 1;
  piVar3 = &DAT_1420a4d60;
  iVar1 = DAT_1420a4d60;
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
  *(int **)(puVar2 + 7) = &DAT_1420a4d60;
  puVar2[5] = uVar4;
  puVar2[6] = 0xffffffff;
  DAT_1421c16d8[0x10] = puVar2 + 1;
  DAT_1421c16d8[1] = FUN_14065dca0;
  DAT_1421c16d8[0xe] = &LAB_14065d980;
  local_res8 = DAT_1421c16d8;
  FUN_140034a30(DAT_1421c16d8 + 3,&local_res8);
  return;
}

