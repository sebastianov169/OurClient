
double FUN_1406f6300(longlong param_1,undefined8 *param_2)

{
  float fVar1;
  int iVar2;
  
  if (*(char *)(param_1 + 0x3f0) != '\0') {
    fVar1 = (float)FUN_140406050();
    return (double)fVar1;
  }
  iVar2 = FUN_140406320(*param_2);
  return (double)iVar2 / DAT_1421b9278;
}

