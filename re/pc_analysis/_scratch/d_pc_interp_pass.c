
void FUN_1407959e0(longlong param_1,undefined8 param_2)

{
  longlong *plVar1;
  longlong *plVar2;
  double dVar3;
  longlong lVar4;
  longlong lVar5;
  int iVar6;
  undefined4 uVar7;
  longlong *plVar8;
  undefined8 *puVar9;
  int iVar10;
  undefined4 uVar11;
  undefined4 uVar12;
  longlong *local_res8;
  longlong local_res18;
  undefined1 local_res20 [8];
  undefined1 local_e8 [8];
  undefined1 local_e0 [8];
  undefined1 local_d8 [8];
  undefined1 local_d0 [8];
  undefined1 local_c8 [8];
  undefined1 local_c0 [8];
  undefined1 local_b8 [8];
  undefined1 local_b0 [8];
  undefined1 local_a8 [8];
  undefined1 local_a0 [8];
  undefined1 local_98 [96];
  
  plVar8 = *(longlong **)(*(longlong *)(param_1 + 0x3a0) + 0x18);
  if ((plVar8 != (longlong *)0x0) && (0 < (int)plVar8[2])) {
    if (*(int *)(*(longlong *)(param_1 + 0x3a0) + 0x10) == 1) {
      local_res8 = (longlong *)0x0;
    }
    else {
      (**(code **)(*plVar8 + 0xb8))(plVar8,&local_res8,0);
    }
    local_res18 = 0;
    FUN_14004fc60(&local_res18,&local_res8);
    lVar4 = local_res18;
    if (local_res18 != 0) {
      iVar10 = 0;
      while( true ) {
        plVar8 = *(longlong **)(lVar4 + 0x18);
        if (plVar8 == (longlong *)0x0) {
          iVar6 = 0;
        }
        else {
          iVar6 = (int)plVar8[2];
        }
        if (iVar6 <= iVar10) break;
        if (*(int *)(lVar4 + 0x10) == 1) {
          local_res8 = (longlong *)0x0;
          iVar10 = iVar10 + 1;
        }
        else {
          (**(code **)(*plVar8 + 0xb8))(plVar8,&local_res8,iVar10);
          iVar10 = iVar10 + 1;
          if (local_res8 != (longlong *)0x0) {
            plVar8 = (longlong *)(**(code **)(*local_res8 + 0xb8))(local_res8,local_res20,0);
            if (((longlong *)*plVar8 != (longlong *)0x0) &&
               (dVar3 = (double)(**(code **)(*(longlong *)*plVar8 + 0x40))(), dVar3 == 0.0)) {
              plVar8 = (longlong *)(**(code **)(*local_res8 + 0xb8))(local_res8,local_e8,1);
              if ((longlong *)*plVar8 == (longlong *)0x0) {
                uVar7 = 0;
              }
              else {
                uVar7 = (**(code **)(*(longlong *)*plVar8 + 0x38))();
              }
              FUN_1409254d0(*(undefined8 *)(param_1 + 0x308),&local_res18,uVar7);
              lVar5 = local_res18;
              if (local_res18 != 0) {
                puVar9 = (undefined8 *)(**(code **)(*local_res8 + 0xb8))(local_res8,local_e0,2);
                plVar8 = (longlong *)*puVar9;
                puVar9 = (undefined8 *)(**(code **)(*local_res8 + 0xb8))(local_res8,local_d8,2);
                plVar1 = (longlong *)*puVar9;
                puVar9 = (undefined8 *)(**(code **)(*local_res8 + 0xb8))(local_res8,local_d0,2);
                plVar2 = (longlong *)*puVar9;
                plVar8 = (longlong *)(**(code **)(*plVar8 + 0xb8))(plVar8,local_c8,4);
                if ((longlong *)*plVar8 == (longlong *)0x0) {
                  uVar7 = 0;
                }
                else {
                  uVar7 = (**(code **)(*(longlong *)*plVar8 + 0x40))();
                }
                plVar8 = (longlong *)(**(code **)(*plVar1 + 0xb8))(plVar1,local_c0,1);
                if ((longlong *)*plVar8 == (longlong *)0x0) {
                  uVar11 = 0;
                }
                else {
                  uVar11 = (**(code **)(*(longlong *)*plVar8 + 0x40))();
                }
                plVar8 = (longlong *)(**(code **)(*plVar2 + 0xb8))(plVar2,local_b8,0);
                if ((longlong *)*plVar8 == (longlong *)0x0) {
                  uVar12 = 0;
                }
                else {
                  uVar12 = (**(code **)(*(longlong *)*plVar8 + 0x40))();
                }
                FUN_1406790f0(lVar5,uVar12,uVar11,uVar7,param_2);
                puVar9 = (undefined8 *)(**(code **)(*local_res8 + 0xb8))(local_res8,local_b0,2);
                plVar8 = (longlong *)
                         (**(code **)(*(longlong *)*puVar9 + 0xb8))((longlong *)*puVar9,local_a8,2);
                if (((longlong *)*plVar8 == (longlong *)0x0) ||
                   (dVar3 = (double)(**(code **)(*(longlong *)*plVar8 + 0x40))(), dVar3 != -1.0)) {
                  puVar9 = (undefined8 *)(**(code **)(*local_res8 + 0xb8))(local_res8,local_a0,2);
                  plVar8 = (longlong *)
                           (**(code **)(*(longlong *)*puVar9 + 0xb8))
                                     ((longlong *)*puVar9,local_98,2);
                  if ((longlong *)*plVar8 == (longlong *)0x0) {
                    uVar7 = 0;
                  }
                  else {
                    uVar7 = (**(code **)(*(longlong *)*plVar8 + 0x40))();
                  }
                  FUN_1406775f0(lVar5,uVar7,(int)param_2);
                }
              }
            }
          }
        }
      }
    }
  }
  return;
}

