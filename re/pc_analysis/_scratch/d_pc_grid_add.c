
void FUN_140926460(longlong param_1,longlong *param_2)

{
  char cVar1;
  longlong local_res10 [3];
  
  cVar1 = (**(code **)(*(longlong *)*param_2 + 400))();
  if (cVar1 == '\0') {
    local_res10[0] = *param_2;
    FUN_1400286d0(*(undefined8 *)(param_1 + 0x18),local_res10);
  }
  local_res10[0] = *param_2;
  FUN_1400286d0(*(undefined8 *)(param_1 + 0x10),local_res10);
  local_res10[0] = *param_2;
  FUN_14005d9f0(*(longlong *)(param_1 + 0x20),*(longlong *)(param_1 + 0x20) + 8,
                *(undefined4 *)(local_res10[0] + 0x2c),local_res10);
  return;
}

