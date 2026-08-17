
void FUN_140924ff0(longlong param_1,longlong *param_2)

{
  uint uVar1;
  longlong *plVar2;
  longlong lVar3;
  char cVar4;
  int iVar5;
  int iVar6;
  uint uVar7;
  int iVar8;
  longlong *plVar9;
  uint uVar10;
  double dVar11;
  double dVar12;
  double dVar13;
  longlong *local_res10;
  longlong *local_res18;
  longlong *local_res20;
  longlong *local_78;
  longlong *local_70 [7];
  
  cVar4 = (**(code **)(*(longlong *)*param_2 + 400))();
  if (cVar4 != '\x01') {
    plVar2 = (longlong *)*param_2;
    lVar3 = *(longlong *)(plVar2[0xb] + 0x10);
    dVar13 = (double)DAT_1421b931c;
    dVar11 = floor((double)*(float *)(lVar3 + 0xc) / dVar13);
    if ((dVar11 < -2147483647.0) || (2147483647.0 < dVar11)) {
      iVar6 = (int)(longlong)dVar11;
    }
    else {
      iVar6 = (int)dVar11;
    }
    dVar11 = (double)iVar6;
    dVar12 = (double)(*(int *)(param_1 + 0x40) + -1);
    if ((dVar12 <= dVar11) && (!NAN(dVar11))) {
      dVar11 = dVar12;
    }
    if ((dVar11 < -2147483647.0) || (2147483647.0 < dVar11)) {
      uVar10 = (uint)(longlong)dVar11;
    }
    else {
      uVar10 = (uint)dVar11;
    }
    dVar11 = floor((double)*(float *)(lVar3 + 0x14) / dVar13);
    if ((dVar11 < -2147483647.0) || (2147483647.0 < dVar11)) {
      iVar6 = (int)(longlong)dVar11;
    }
    else {
      iVar6 = (int)dVar11;
    }
    dVar11 = (double)iVar6;
    dVar13 = (double)(*(int *)(param_1 + 0x44) + -1);
    if ((dVar13 <= dVar11) && (!NAN(dVar11))) {
      dVar11 = dVar13;
    }
    if ((dVar11 < -2147483647.0) || (2147483647.0 < dVar11)) {
      uVar7 = (uint)(longlong)dVar11;
    }
    else {
      uVar7 = (uint)dVar11;
    }
    if ((*(uint *)((longlong)plVar2 + 0xdc) != uVar10) || (*(uint *)(plVar2 + 0x1c) != uVar7)) {
      plVar9 = (longlong *)0x0;
      if (*(uint *)((longlong)plVar2 + 0xdc) != 0xffffffff) {
        local_78 = (longlong *)0x0;
        local_res10 = plVar9;
        local_70[0] = plVar2;
        if (((*(uint *)(plVar2 + 0x1c) < *(uint *)(*(longlong *)(param_1 + 0x30) + 0x10)) &&
            (local_res20 = *(longlong **)
                            (*(longlong *)(*(longlong *)(param_1 + 0x30) + 0x18) +
                            (longlong)(int)*(uint *)(plVar2 + 0x1c) * 8), local_res10 = local_res20,
            local_res20 != (longlong *)0x0)) && ((int)local_res20[1] != -1)) {
          local_res10 = (longlong *)0x0;
          FUN_140028e80(&local_res10,&local_res20,0);
        }
        local_res18 = plVar9;
        if (((*(uint *)((longlong)plVar2 + 0xdc) < *(uint *)(local_res10 + 2)) &&
            (local_res20 = *(longlong **)
                            (local_res10[3] + (longlong)(int)*(uint *)((longlong)plVar2 + 0xdc) * 8)
            , local_res18 = local_res20, local_res20 != (longlong *)0x0)) &&
           ((int)local_res20[1] != -1)) {
          local_res18 = (longlong *)0x0;
          FUN_140028e80(&local_res18,&local_res20,0);
        }
        iVar6 = FUN_140028530(local_res18,local_70,&local_78);
        lVar3 = *param_2;
        uVar1 = *(uint *)(lVar3 + 0xe0);
        local_res20 = plVar9;
        if (((uVar1 < *(uint *)(*(longlong *)(param_1 + 0x30) + 0x10)) &&
            (local_70[0] = *(longlong **)
                            (*(longlong *)(*(longlong *)(param_1 + 0x30) + 0x18) +
                            (longlong)(int)uVar1 * 8), local_res20 = local_70[0],
            local_70[0] != (longlong *)0x0)) && ((int)local_70[0][1] != -1)) {
          local_res20 = (longlong *)0x0;
          FUN_140028e80(&local_res20,local_70,0);
        }
        uVar1 = *(uint *)(lVar3 + 0xdc);
        local_78 = plVar9;
        if (((uVar1 < *(uint *)(local_res20 + 2)) &&
            (local_70[0] = *(longlong **)(local_res20[3] + (longlong)(int)uVar1 * 8),
            local_78 = local_70[0], local_70[0] != (longlong *)0x0)) && ((int)local_70[0][1] != -1))
        {
          local_78 = (longlong *)0x0;
          FUN_140028e80(&local_78,local_70,0);
        }
        plVar2 = local_78;
        iVar5 = (int)local_78[2];
        iVar8 = 1;
        if (iVar6 < iVar5) {
          if ((iVar6 < 0) && (iVar6 = iVar5 + iVar6, iVar6 < 0)) {
            iVar6 = 0;
          }
          if (iVar5 < iVar6 + 1) {
            iVar8 = iVar5 - iVar6;
          }
          iVar5 = (**(code **)(*local_78 + 0x110))(local_78);
          FUN_141bedfa0((longlong)(iVar5 * iVar6) + plVar2[3],
                        (longlong)((iVar6 + iVar8) * iVar5) + plVar2[3],
                        (longlong)((((int)plVar2[2] - iVar6) - iVar8) * iVar5));
          FUN_140021c20(plVar2,(int)plVar2[2] - iVar8);
        }
      }
      *(uint *)(*param_2 + 0xdc) = uVar10;
      *(uint *)(*param_2 + 0xe0) = uVar7;
      local_70[0] = (longlong *)*param_2;
      local_res10 = (longlong *)0x0;
      if (((uVar7 < *(uint *)(*(longlong *)(param_1 + 0x30) + 0x10)) &&
          (local_res20 = *(longlong **)
                          (*(longlong *)(*(longlong *)(param_1 + 0x30) + 0x18) +
                          (longlong)(int)uVar7 * 8), local_res10 = local_res20,
          local_res20 != (longlong *)0x0)) && ((int)local_res20[1] != -1)) {
        local_res10 = (longlong *)0x0;
        FUN_140028e80(&local_res10,&local_res20,0);
      }
      local_res18 = (longlong *)0x0;
      if (((uVar10 < *(uint *)(local_res10 + 2)) &&
          (local_res20 = *(longlong **)(local_res10[3] + (longlong)(int)uVar10 * 8),
          local_res18 = local_res20, local_res20 != (longlong *)0x0)) && ((int)local_res20[1] != -1)
         ) {
        local_res18 = (longlong *)0x0;
        FUN_140028e80(&local_res18,&local_res20,0);
      }
      FUN_1400286d0(local_res18,local_70);
    }
  }
  return;
}

