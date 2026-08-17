
uint FUN_140406320(longlong param_1)

{
  int iVar1;
  uint uVar2;
  double dVar3;
  
  iVar1 = FUN_140406270();
  uVar2 = FUN_140406270(param_1);
  if ((*(longlong **)(param_1 + 0x20) != (longlong *)0x0) &&
     (dVar3 = (double)(**(code **)(**(longlong **)(param_1 + 0x20) + 0x40))(), dVar3 == 1.0)) {
    return iVar1 + uVar2 * 0x100;
  }
  return iVar1 << 8 | uVar2;
}

