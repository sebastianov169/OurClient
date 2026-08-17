
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

undefined8 FUN_1407be550(int *param_1,longlong *param_2)

{
  undefined8 *puVar1;
  char cVar2;
  uint *puVar3;
  undefined4 extraout_XMM0_Da;
  undefined4 extraout_XMM0_Da_00;
  undefined4 extraout_XMM0_Da_01;
  undefined4 extraout_XMM0_Da_02;
  undefined4 extraout_XMM0_Da_03;
  undefined4 extraout_XMM0_Da_04;
  undefined4 extraout_XMM0_Da_05;
  undefined4 extraout_XMM0_Da_06;
  undefined4 extraout_XMM0_Da_07;
  undefined4 extraout_XMM0_Da_08;
  undefined4 extraout_XMM0_Da_09;
  undefined4 extraout_XMM0_Da_10;
  undefined4 extraout_XMM0_Da_11;
  undefined4 extraout_XMM0_Da_12;
  undefined4 extraout_XMM0_Da_13;
  undefined4 extraout_XMM0_Db;
  undefined4 extraout_XMM0_Db_00;
  undefined4 extraout_XMM0_Db_01;
  undefined4 extraout_XMM0_Db_02;
  undefined4 extraout_XMM0_Db_03;
  undefined4 extraout_XMM0_Db_04;
  undefined4 extraout_XMM0_Db_05;
  undefined4 extraout_XMM0_Db_06;
  undefined4 extraout_XMM0_Db_07;
  undefined4 extraout_XMM0_Db_08;
  undefined4 extraout_XMM0_Db_09;
  undefined4 extraout_XMM0_Db_10;
  undefined4 extraout_XMM0_Db_11;
  undefined4 extraout_XMM0_Db_12;
  undefined4 extraout_XMM0_Db_13;
  undefined8 local_res8;
  uint local_18 [2];
  undefined8 local_10;
  
  switch(*param_1 + -9) {
  case 0:
    cVar2 = FUN_1407b3ca0(param_1);
    if (cVar2 != '\0') {
      cVar2 = FUN_140052590(&local_res8,*param_2);
      if (cVar2 != '\0') {
        DAT_1421c1838 = (undefined8 *)local_res8;
        return 1;
      }
      puVar1 = (undefined8 *)*param_2;
      if (puVar1 != (undefined8 *)0x0) {
        cVar2 = (**(code **)*puVar1)(puVar1,0x50b86242);
        DAT_1421c1838 = (undefined8 *)0x0;
        if (cVar2 != '\0') {
          DAT_1421c1838 = puVar1;
        }
        return 1;
      }
      DAT_1421c1838 = (undefined8 *)0x0;
      return 1;
    }
    break;
  case 1:
    cVar2 = FUN_1407b3d50(param_1);
    if (cVar2 != '\0') {
      local_res8 = 0;
      FUN_140029780(&local_res8,param_2,0);
      DAT_1421c17c0 = local_res8;
      return 1;
    }
    cVar2 = FUN_1407b3e10(param_1);
    if (cVar2 != '\0') {
      local_res8 = 0;
      FUN_14004fc60(&local_res8,param_2);
      DAT_1421c17e8 = local_res8;
      return 1;
    }
    cVar2 = FUN_1407b3ed0(param_1);
    if (cVar2 != '\0') {
      param_2 = (longlong *)*param_2;
      if (param_2 == (longlong *)0x0) {
        DAT_1421c1800 = 0;
        puVar3 = local_18;
        local_10 = 0;
      }
      else {
        puVar3 = (uint *)(**(code **)(*param_2 + 0x58))(param_2,local_18);
        DAT_1421c1800 = *puVar3;
      }
      DAT_1421c1808 = *(undefined8 *)(puVar3 + 2);
      return 1;
    }
    break;
  case 2:
    cVar2 = FUN_1407b3f90(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b9310 = CONCAT44(extraout_XMM0_Db,extraout_XMM0_Da);
        return 1;
      }
      DAT_1421b9310 = 0;
      return 1;
    }
    cVar2 = FUN_1407b4060(param_1);
    if (cVar2 != '\0') {
      cVar2 = FUN_140052590(&local_res8,*param_2);
      if (cVar2 != '\0') {
        DAT_1421c1840 = (undefined8 *)local_res8;
        return 1;
      }
      puVar1 = (undefined8 *)*param_2;
      if (puVar1 != (undefined8 *)0x0) {
        cVar2 = (**(code **)*puVar1)(puVar1,0x50b86242);
        DAT_1421c1840 = (undefined8 *)0x0;
        if (cVar2 != '\0') {
          DAT_1421c1840 = puVar1;
        }
        return 1;
      }
      DAT_1421c1840 = (undefined8 *)0x0;
      return 1;
    }
    break;
  case 3:
    cVar2 = FUN_1407b4130(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b930c = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b930c = 0;
      return 1;
    }
    cVar2 = FUN_1407b4210(param_1);
    if (cVar2 != '\0') {
      DAT_1421b9301 = FUN_1400af970(param_2);
      return 1;
    }
    break;
  case 4:
    cVar2 = FUN_1407b43e0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b9278 = CONCAT44(extraout_XMM0_Db_00,extraout_XMM0_Da_00);
        return 1;
      }
      DAT_1421b9278 = 0;
      return 1;
    }
    cVar2 = FUN_1407b44d0(param_1);
    if (cVar2 != '\0') {
      param_2 = (longlong *)*param_2;
      if (param_2 == (longlong *)0x0) {
        _DAT_1421c1820 = 0;
        puVar3 = local_18;
        local_10 = 0;
      }
      else {
        puVar3 = (uint *)(**(code **)(*param_2 + 0x58))(param_2,local_18);
        _DAT_1421c1820 = *puVar3;
      }
      DAT_1421c1828 = *(undefined8 *)(puVar3 + 2);
      return 1;
    }
    cVar2 = FUN_1407b45c0(param_1);
    if (cVar2 != '\0') {
      DAT_1421b8d92 = FUN_1400af970(param_2);
      return 1;
    }
    break;
  case 6:
    cVar2 = FUN_1407b47b0(param_1);
    if (cVar2 != '\0') {
      DAT_1421b9303 = FUN_1400af970(param_2);
      return 1;
    }
    cVar2 = FUN_1407b48b0(param_1);
    if (cVar2 != '\0') {
      param_2 = (longlong *)*param_2;
      if (param_2 == (longlong *)0x0) {
        _DAT_1421c1810 = 0;
        puVar3 = local_18;
        local_10 = 0;
      }
      else {
        puVar3 = (uint *)(**(code **)(*param_2 + 0x58))(param_2,local_18);
        _DAT_1421c1810 = *puVar3;
      }
      DAT_1421c1818 = *(undefined8 *)(puVar3 + 2);
      return 1;
    }
    cVar2 = FUN_1407b49b0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b926c = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b926c = 0;
      return 1;
    }
    cVar2 = FUN_1407b4ab0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b92a0 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b92a0 = 0;
      return 1;
    }
    cVar2 = FUN_1407b4bb0(param_1);
    if (cVar2 != '\0') {
      DAT_1421c1830 = *param_2;
      return 1;
    }
    cVar2 = FUN_1407b4cb0(param_1);
    if (cVar2 != '\0') {
      DAT_1421b9300 = FUN_1400af970(param_2);
      return 1;
    }
    break;
  case 7:
    cVar2 = FUN_1407b4eb0(param_1);
    if (cVar2 != '\0') {
      cVar2 = FUN_140052590(&local_res8,*param_2);
      if (cVar2 != '\0') {
        DAT_1421c17a8 = (undefined8 *)local_res8;
        return 1;
      }
      puVar1 = (undefined8 *)*param_2;
      if (puVar1 != (undefined8 *)0x0) {
        cVar2 = (**(code **)*puVar1)(puVar1,0xb2a1d57);
        DAT_1421c17a8 = (undefined8 *)0x0;
        if (cVar2 != '\0') {
          DAT_1421c17a8 = puVar1;
        }
        return 1;
      }
      DAT_1421c17a8 = (undefined8 *)0x0;
      return 1;
    }
    cVar2 = FUN_1407b4fc0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b9308 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b9308 = 0;
      return 1;
    }
    cVar2 = FUN_1407b50d0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b9288 = CONCAT44(extraout_XMM0_Db_01,extraout_XMM0_Da_01);
        return 1;
      }
      DAT_1421b9288 = 0;
      return 1;
    }
    cVar2 = FUN_1407b51e0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b9290 = CONCAT44(extraout_XMM0_Db_02,extraout_XMM0_Da_02);
        return 1;
      }
      DAT_1421b9290 = 0;
      return 1;
    }
    cVar2 = FUN_1407b52f0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b9298 = CONCAT44(extraout_XMM0_Db_03,extraout_XMM0_Da_03);
        return 1;
      }
      DAT_1421b9298 = 0;
      return 1;
    }
    cVar2 = FUN_1407b5400(param_1);
    if (cVar2 != '\0') {
      cVar2 = FUN_140052590(&local_res8,*param_2);
      if (cVar2 != '\0') {
        DAT_1421c1848 = (undefined8 *)local_res8;
        return 1;
      }
      puVar1 = (undefined8 *)*param_2;
      if (puVar1 != (undefined8 *)0x0) {
        cVar2 = (**(code **)*puVar1)(puVar1,0x50b86242);
        DAT_1421c1848 = (undefined8 *)0x0;
        if (cVar2 != '\0') {
          DAT_1421c1848 = puVar1;
        }
        return 1;
      }
      DAT_1421c1848 = (undefined8 *)0x0;
      return 1;
    }
    break;
  case 8:
    cVar2 = FUN_1407b5630(param_1);
    if (cVar2 != '\0') {
      cVar2 = FUN_140052590(&local_res8,*param_2);
      if (cVar2 != '\0') {
        DAT_1421c17b0 = (undefined8 *)local_res8;
        return 1;
      }
      puVar1 = (undefined8 *)*param_2;
      if (puVar1 != (undefined8 *)0x0) {
        cVar2 = (**(code **)*puVar1)(puVar1,0x4b4897d9);
        DAT_1421c17b0 = (undefined8 *)0x0;
        if (cVar2 != '\0') {
          DAT_1421c17b0 = puVar1;
        }
        return 1;
      }
      DAT_1421c17b0 = (undefined8 *)0x0;
      return 1;
    }
    cVar2 = FUN_1407b5750(param_1);
    if (cVar2 != '\0') {
      DAT_1421b9302 = FUN_1400af970(param_2);
      return 1;
    }
    cVar2 = FUN_1407b5870(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b9304 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b9304 = 0;
      return 1;
    }
    break;
  case 9:
    cVar2 = FUN_1407b5ab0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b92e8 = CONCAT44(extraout_XMM0_Db_04,extraout_XMM0_Da_04);
        return 1;
      }
      DAT_1421b92e8 = 0;
      return 1;
    }
    cVar2 = FUN_1407b5be0(param_1);
    if (cVar2 != '\0') {
      DAT_1421b8d91 = FUN_1400af970(param_2);
      return 1;
    }
    cVar2 = FUN_1407b5d10(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b92e0 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b92e0 = 0;
      return 1;
    }
    cVar2 = FUN_1407b5e40(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b92d8 = CONCAT44(extraout_XMM0_Db_05,extraout_XMM0_Da_05);
        return 1;
      }
      DAT_1421b92d8 = 0;
      return 1;
    }
    break;
  case 10:
    cVar2 = FUN_1407b5f70(param_1);
    if (cVar2 != '\0') {
      param_2 = (longlong *)*param_2;
      if (param_2 == (longlong *)0x0) {
        DAT_1421c17c8 = 0;
        puVar3 = local_18;
        local_10 = 0;
      }
      else {
        puVar3 = (uint *)(**(code **)(*param_2 + 0x58))(param_2,local_18);
        DAT_1421c17c8 = *puVar3;
      }
      DAT_1421c17d0 = *(undefined8 *)(puVar3 + 2);
      return 1;
    }
    cVar2 = FUN_1407b60b0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b92f0 = CONCAT44(extraout_XMM0_Db_06,extraout_XMM0_Da_06);
        return 1;
      }
      DAT_1421b92f0 = 0;
      return 1;
    }
    cVar2 = FUN_1407b61f0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b92d0 = CONCAT44(extraout_XMM0_Db_07,extraout_XMM0_Da_07);
        return 1;
      }
      DAT_1421b92d0 = 0;
      return 1;
    }
    cVar2 = FUN_1407b6330(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b9320 = CONCAT44(extraout_XMM0_Db_08,extraout_XMM0_Da_08);
        return 1;
      }
      DAT_1421b9320 = 0;
      return 1;
    }
    break;
  case 0xb:
    cVar2 = FUN_1407b65b0(param_1);
    if (cVar2 != '\0') {
      param_2 = (longlong *)*param_2;
      if (param_2 == (longlong *)0x0) {
        DAT_1421c17d8 = 0;
        puVar3 = local_18;
        local_10 = 0;
      }
      else {
        puVar3 = (uint *)(**(code **)(*param_2 + 0x58))(param_2,local_18);
        DAT_1421c17d8 = *puVar3;
      }
      DAT_1421c17e0 = *(undefined8 *)(puVar3 + 2);
      return 1;
    }
    cVar2 = FUN_1407b66f0(param_1);
    if (cVar2 != '\0') {
      param_2 = (longlong *)*param_2;
      if (param_2 == (longlong *)0x0) {
        _DAT_1421c17f0 = 0;
        puVar3 = local_18;
        local_10 = 0;
      }
      else {
        puVar3 = (uint *)(**(code **)(*param_2 + 0x58))(param_2,local_18);
        _DAT_1421c17f0 = *puVar3;
      }
      DAT_1421c17f8 = *(undefined8 *)(puVar3 + 2);
      return 1;
    }
    break;
  case 0xc:
    cVar2 = FUN_1407b6830(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b92a8 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b92a8 = 0;
      return 1;
    }
    cVar2 = FUN_1407b6980(param_1);
    if (cVar2 != '\0') {
      DAT_1421b8d93 = FUN_1400af970(param_2);
      return 1;
    }
    cVar2 = FUN_1407b6ad0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b9270 = CONCAT44(extraout_XMM0_Db_09,extraout_XMM0_Da_09);
        return 1;
      }
      DAT_1421b9270 = 0;
      return 1;
    }
    break;
  case 0xd:
    cVar2 = FUN_1407b6d70(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b92e4 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b92e4 = 0;
      return 1;
    }
    cVar2 = FUN_1407b6ed0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b9318 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b9318 = 0;
      return 1;
    }
    break;
  case 0xe:
    cVar2 = FUN_1407b7030(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b92f8 = CONCAT44(extraout_XMM0_Db_10,extraout_XMM0_Da_10);
        return 1;
      }
      DAT_1421b92f8 = 0;
      return 1;
    }
    cVar2 = FUN_1407b71a0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b92c0 = CONCAT44(extraout_XMM0_Db_11,extraout_XMM0_Da_11);
        return 1;
      }
      DAT_1421b92c0 = 0;
      return 1;
    }
    cVar2 = FUN_1407b7310(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b92c8 = CONCAT44(extraout_XMM0_Db_12,extraout_XMM0_Da_12);
        return 1;
      }
      DAT_1421b92c8 = 0;
      return 1;
    }
    cVar2 = FUN_1407b7480(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b92a4 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b92a4 = 0;
      return 1;
    }
    break;
  case 0xf:
    cVar2 = FUN_1407b75f0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b92b0 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b92b0 = 0;
      return 1;
    }
    cVar2 = FUN_1407b7770(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b92ac = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b92ac = 0;
      return 1;
    }
    break;
  case 0x10:
    cVar2 = FUN_1407b78f0(param_1);
    if (cVar2 != '\0') {
      cVar2 = FUN_140052590(&local_res8,*param_2);
      if (cVar2 != '\0') {
        DAT_1421c17b8 = (undefined8 *)local_res8;
        return 1;
      }
      puVar1 = (undefined8 *)*param_2;
      if (puVar1 != (undefined8 *)0x0) {
        cVar2 = (**(code **)*puVar1)(puVar1,0x3c3ecb20);
        DAT_1421c17b8 = (undefined8 *)0x0;
        if (cVar2 != '\0') {
          DAT_1421c17b8 = puVar1;
        }
        return 1;
      }
      DAT_1421c17b8 = (undefined8 *)0x0;
      return 1;
    }
    cVar2 = FUN_1407b7a70(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        (**(code **)(*(longlong *)*param_2 + 0x40))();
        DAT_1421b92b8 = CONCAT44(extraout_XMM0_Db_13,extraout_XMM0_Da_13);
        return 1;
      }
      DAT_1421b92b8 = 0;
      return 1;
    }
    cVar2 = FUN_1407b7bf0(param_1);
    if (cVar2 != '\0') {
      if ((longlong *)*param_2 != (longlong *)0x0) {
        DAT_1421b92b4 = (**(code **)(*(longlong *)*param_2 + 0x38))();
        return 1;
      }
      DAT_1421b92b4 = 0;
      return 1;
    }
  }
  return 0;
}

