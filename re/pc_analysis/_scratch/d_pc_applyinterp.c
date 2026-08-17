
undefined8 * FUN_140795d70(undefined8 *param_1,undefined8 param_2,longlong *param_3)

{
  undefined4 uVar1;
  
  if ((longlong *)*param_3 == (longlong *)0x0) {
    uVar1 = 0;
  }
  else {
    uVar1 = (**(code **)(*(longlong *)*param_3 + 0x40))();
  }
  FUN_1407959e0(param_2,uVar1);
  *param_1 = 0;
  return param_1;
}

