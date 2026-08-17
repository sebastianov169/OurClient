
uint FUN_140406050(longlong param_1)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  double dVar5;
  
  uVar1 = FUN_140406270();
  uVar2 = FUN_140406270(param_1);
  uVar3 = FUN_140406270(param_1);
  uVar4 = FUN_140406270(param_1);
  if ((*(longlong **)(param_1 + 0x20) == (longlong *)0x0) ||
     (dVar5 = (double)(**(code **)(**(longlong **)(param_1 + 0x20) + 0x40))(), dVar5 != 1.0)) {
    uVar1 = ((uVar1 << 8 | uVar2) << 8 | uVar3) << 8 | uVar4;
  }
  else {
    uVar1 = ((uVar4 << 8 | uVar3) << 8 | uVar2) << 8 | uVar1;
  }
  return uVar1;
}

