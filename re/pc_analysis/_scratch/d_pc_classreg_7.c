
void FUN_1414c4ee0(void)

{
  undefined8 *puVar1;
  int iVar2;
  undefined4 *puVar3;
  int *piVar4;
  undefined8 *puVar5;
  uint uVar6;
  undefined8 *puVar7;
  undefined8 *local_res8;
  undefined4 uStack_1c;
  
  puVar3 = (undefined4 *)_malloc_base(0x8c);
  puVar1 = (undefined8 *)(puVar3 + 1);
  *puVar3 = 0x80000000;
  FUN_141bedde0(puVar1,0,0x88);
  puVar5 = (undefined8 *)0x0;
  uVar6 = 0;
  puVar7 = puVar5;
  if (puVar1 != (undefined8 *)0x0) {
    *(undefined8 *)(puVar3 + 5) = 0;
    *puVar1 = hx::Class_obj::vftable;
    puVar3[7] = 0;
    *(undefined8 *)(puVar3 + 9) = 0;
    *(undefined8 *)(puVar3 + 0xb) = 0;
    puVar3[0xd] = 0;
    *(undefined8 *)(puVar3 + 0xf) = 0;
    *(undefined8 *)(puVar3 + 0x1f) = 0;
    *(undefined8 *)(puVar3 + 0x21) = 0;
    puVar7 = puVar1;
  }
  DAT_1421cc3b0 = puVar7;
  puVar7[4] = "fkengine.game.entities.ChestEntity";
  *(undefined4 *)(puVar7 + 3) = 0x22;
  DAT_1421cc3b0[2] = &DAT_1421cc3c8;
  DAT_1421cc3b0[9] = FUN_1414c3ee0;
  DAT_1421cc3b0[8] = FUN_1414c3fb0;
  DAT_1421cc3b0[0xb] = FUN_140022100;
  DAT_1421cc3b0[0xc] = FUN_140022100;
  DAT_1421cc3b0[0xf] = 0;
  piVar4 = &DAT_1420f5300;
  iVar2 = DAT_1420f5300;
  while (iVar2 != 0) {
    uVar6 = (int)puVar5 + 1;
    puVar5 = (undefined8 *)(ulonglong)uVar6;
    piVar4 = piVar4 + 4;
    iVar2 = *piVar4;
  }
  puVar3 = (undefined4 *)_malloc_base(0x24);
  *puVar3 = 0x80000000;
  puVar3[1] = 0x41d32178;
  puVar3[2] = 1;
  puVar3[3] = 0xfffffffe;
  puVar3[4] = uStack_1c;
  puVar3[5] = 0;
  puVar3[6] = 0;
  puVar3[7] = 0;
  puVar3[8] = 0;
  *(int **)(puVar3 + 7) = &DAT_1420f5300;
  puVar3[5] = uVar6;
  puVar3[6] = 0xffffffff;
  DAT_1421cc3b0[0x10] = puVar3 + 1;
  DAT_1421cc3b0[1] = FUN_1414c5090;
  local_res8 = DAT_1421cc3b0;
  FUN_140034a30(DAT_1421cc3b0 + 3,&local_res8);
  return;
}

