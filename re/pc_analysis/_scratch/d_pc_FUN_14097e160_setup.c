
int * FUN_14097e160(longlong param_1,int *param_2,int *param_3,int param_4)

{
  byte *pbVar1;
  longlong lVar2;
  char cVar3;
  int iVar4;
  longlong *plVar5;
  undefined8 *puVar6;
  undefined8 local_res18 [2];
  undefined8 local_128;
  undefined8 local_120;
  undefined8 local_118;
  undefined8 local_110;
  undefined8 local_108;
  undefined8 local_100;
  undefined8 local_f8;
  undefined8 local_f0;
  undefined8 local_e8;
  undefined8 local_e0;
  undefined8 local_d8;
  undefined8 local_d0;
  undefined8 local_c8;
  undefined8 local_c0;
  undefined8 local_b8;
  undefined8 local_b0;
  undefined8 local_a8;
  undefined8 local_a0;
  undefined8 local_98;
  undefined8 local_90;
  undefined8 local_88;
  undefined8 local_80;
  undefined8 local_78;
  undefined8 local_70;
  undefined8 local_68;
  undefined8 local_60;
  undefined8 local_58;
  undefined8 local_50;
  undefined8 local_48;
  undefined8 local_40;
  undefined8 local_38;
  undefined8 local_30;
  undefined8 local_28 [2];
  
  switch(*param_3) {
  case 5:
    if ((((*param_3 == 5) && (iVar4 = FUN_140051080(param_3), iVar4 == 0x1035bfc5)) &&
        (pbVar1 = *(byte **)(param_3 + 2),
        (((((*pbVar1 ^ 0x811c9dc5) * 0x83 ^ (uint)pbVar1[1]) * 0x83 ^ (uint)pbVar1[2]) * 0x83 ^
         (uint)pbVar1[3]) * 0x83 ^ (uint)pbVar1[4]) * 0x83 == 0x3e1981a2)) && (param_4 == 2)) {
      iVar4 = FUN_14092ca30(param_1);
      *param_2 = iVar4;
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_14097fe40(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x30);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_14097fec0(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0x7c);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_14097ff40(param_3);
    if (cVar3 == '\0') {
      cVar3 = FUN_14097ffc0(param_3);
      if (cVar3 == '\0') break;
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "write";
        *puVar6 = hx::CMemberFunction2::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_1409645e0;
        goto LAB_14097fda6;
      }
    }
    else {
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "start";
        *puVar6 = hx::CMemberFunction3::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_140945da0;
        goto LAB_14097fda6;
      }
    }
    goto LAB_14097e30f;
  case 6:
    cVar3 = FUN_140980040(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x10);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409800d0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x48);
      param_2[3] = *(int *)(param_1 + 0x40);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_140980160(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x60);
      param_2[3] = *(int *)(param_1 + 0x58);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_1409801f0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x110);
      param_2[3] = *(int *)(param_1 + 0x108);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_140980280(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x1ac);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_14054cb00(param_3);
    if (cVar3 == '\0') {
      cVar3 = FUN_140980310(param_3);
      if (cVar3 == '\0') break;
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "freeze";
        *puVar6 = hx::CMemberFunction0::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_14096db90;
        goto LAB_14097fda6;
      }
    }
    else {
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "loaded";
        *puVar6 = hx::CMemberFunction2::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_1401a3ff0;
        goto LAB_14097fda6;
      }
    }
    goto LAB_14097e30f;
  case 7:
    cVar3 = FUN_1409803a0(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x38);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140980430(param_3);
    if (cVar3 == '\0') {
      cVar3 = FUN_1409804c0(param_3);
      if (cVar3 == '\0') break;
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "process";
        *puVar6 = hx::CMemberFunction0::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_140016300;
        goto LAB_14097fda6;
      }
    }
    else {
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "connect";
        *puVar6 = hx::CMemberFunction2::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_14093e900;
        goto LAB_14097fda6;
      }
    }
    goto LAB_14097e30f;
  case 8:
    cVar3 = FUN_140980550(param_3);
    if ((cVar3 != '\0') && (param_4 == 2)) {
LAB_14097e763:
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x20);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409805f0(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x120);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140980690(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x144);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140980730(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x160);
      param_2[3] = *(int *)(param_1 + 0x158);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_1409807d0(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0x1b0);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_140980870(param_3);
    if (cVar3 == '\0') break;
    if ((int)(DWORD)DAT_1421bb758 < 0x40) {
      plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
    }
    else {
      plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
    }
    puVar6 = (undefined8 *)plVar5[1];
    if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
      puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
    }
    else {
      plVar5[1] = (longlong)puVar6 + 0x24U;
      *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
    }
    (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
    if (puVar6 != (undefined8 *)0x0) {
      *(undefined8 **)param_2 = puVar6;
      puVar6[3] = "supports";
      *puVar6 = hx::CMemberFunction1::vftable;
      puVar6[1] = param_1;
      puVar6[2] = FUN_14092c980;
      goto LAB_14097fda6;
    }
    goto LAB_14097e30f;
  case 9:
    cVar3 = FUN_140980910(param_3);
    if ((cVar3 != '\0') && (param_4 == 2)) {
      if ((*(char *)(param_1 + 0xd8) == '\0') && (*(longlong *)(param_1 + 0x98) != 0)) {
        *(undefined1 *)param_2 = *(undefined1 *)(*(longlong *)(param_1 + 0x98) + 0x38);
        param_2[2] = 5;
        return param_2;
      }
LAB_14097e8e4:
      param_2[2] = 5;
      *(undefined1 *)param_2 = 0;
      return param_2;
    }
    cVar3 = FUN_1409809c0(param_3);
    if (cVar3 != '\0') goto LAB_14097e763;
    cVar3 = FUN_140980a70(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x50);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140980b20(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x68);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140980bd0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x80);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140980c80(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0xac);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140980d30(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x130);
      param_2[3] = *(int *)(param_1 + 0x128);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_140980de0(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x138);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140980e90(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x150);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140980f40(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x198);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140980ff0(param_3);
    if (cVar3 == '\0') {
      cVar3 = FUN_1409810a0(param_3);
      if (cVar3 == '\0') {
        cVar3 = FUN_140981150(param_3);
        if (cVar3 == '\0') {
          cVar3 = FUN_140981200(param_3);
          if (cVar3 == '\0') break;
          if ((int)(DWORD)DAT_1421bb758 < 0x40) {
            plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
          }
          else {
            plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
          }
          puVar6 = (undefined8 *)plVar5[1];
          if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
            puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
          }
          else {
            plVar5[1] = (longlong)puVar6 + 0x24U;
            *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
          }
          (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
          if (puVar6 != (undefined8 *)0x0) {
            *(undefined8 **)param_2 = puVar6;
            puVar6[3] = "closeConn";
            *puVar6 = hx::CMemberFunction1::vftable;
            puVar6[1] = param_1;
            puVar6[2] = FUN_1409779f0;
            goto LAB_14097fda6;
          }
        }
        else {
          if ((int)(DWORD)DAT_1421bb758 < 0x40) {
            plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
          }
          else {
            plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
          }
          puVar6 = (undefined8 *)plVar5[1];
          if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
            puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
          }
          else {
            plVar5[1] = (longlong)puVar6 + 0x24U;
            *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
          }
          (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
          if (puVar6 != (undefined8 *)0x0) {
            *(undefined8 **)param_2 = puVar6;
            puVar6[3] = "mediaPing";
            *puVar6 = hx::CMemberFunction0::vftable;
            puVar6[1] = param_1;
            puVar6[2] = FUN_1409662c0;
            goto LAB_14097fda6;
          }
        }
      }
      else {
        if ((int)(DWORD)DAT_1421bb758 < 0x40) {
          plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
        }
        else {
          plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
        }
        puVar6 = (undefined8 *)plVar5[1];
        if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
          puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
        }
        else {
          plVar5[1] = (longlong)puVar6 + 0x24U;
          *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
        }
        (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
        if (puVar6 != (undefined8 *)0x0) {
          *(undefined8 **)param_2 = puVar6;
          puVar6[3] = "getStrKey";
          *puVar6 = hx::CMemberFunction1::vftable;
          puVar6[1] = param_1;
          puVar6[2] = FUN_14093ac90;
          goto LAB_14097fda6;
        }
      }
    }
    else {
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "get_timer";
        *puVar6 = hx::CMemberFunction0::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_14092cac0;
        goto LAB_14097fda6;
      }
    }
    goto LAB_14097e30f;
  case 10:
    cVar3 = FUN_1409812b0(param_3);
    if ((cVar3 != '\0') && (param_4 == 2)) {
LAB_14097eccd:
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x90);
      param_2[3] = *(int *)(param_1 + 0x88);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_140981370(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0x34);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_140981430(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0xc0);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_1409814f0(param_3);
    if (cVar3 == '\0') {
      cVar3 = FUN_1409815b0(param_3);
      if (cVar3 == '\0') {
        cVar3 = FUN_140981670(param_3);
        if (cVar3 == '\0') {
          cVar3 = FUN_140981730(param_3);
          if (cVar3 == '\0') break;
          if ((int)(DWORD)DAT_1421bb758 < 0x40) {
            plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
          }
          else {
            plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
          }
          puVar6 = (undefined8 *)plVar5[1];
          if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
            puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
          }
          else {
            plVar5[1] = (longlong)puVar6 + 0x24U;
            *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
          }
          (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
          if (puVar6 != (undefined8 *)0x0) {
            *(undefined8 **)param_2 = puVar6;
            puVar6[3] = "disconnect";
            *puVar6 = hx::CMemberFunction0::vftable;
            puVar6[1] = param_1;
            puVar6[2] = FUN_140972a90;
            goto LAB_14097fda6;
          }
        }
        else {
          if ((int)(DWORD)DAT_1421bb758 < 0x40) {
            plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
          }
          else {
            plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
          }
          puVar6 = (undefined8 *)plVar5[1];
          if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
            puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
          }
          else {
            plVar5[1] = (longlong)puVar6 + 0x24U;
            *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
          }
          (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
          if (puVar6 != (undefined8 *)0x0) {
            *(undefined8 **)param_2 = puVar6;
            puVar6[3] = "sendPacket";
            *puVar6 = hx::CMemberFunction1::vftable;
            puVar6[1] = param_1;
            puVar6[2] = FUN_1409703e0;
            goto LAB_14097fda6;
          }
        }
      }
      else {
        if ((int)(DWORD)DAT_1421bb758 < 0x40) {
          plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
        }
        else {
          plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
        }
        puVar6 = (undefined8 *)plVar5[1];
        if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
          puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
        }
        else {
          plVar5[1] = (longlong)puVar6 + 0x24U;
          *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
        }
        (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
        if (puVar6 != (undefined8 *)0x0) {
          *(undefined8 **)param_2 = puVar6;
          puVar6[3] = "writeClear";
          *puVar6 = hx::CMemberFunction2::vftable;
          puVar6[1] = param_1;
          puVar6[2] = FUN_14096fd00;
          goto LAB_14097fda6;
        }
      }
    }
    else {
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "getByteKey";
        *puVar6 = hx::CMemberFunction1::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_14093ade0;
        goto LAB_14097fda6;
      }
    }
    goto LAB_14097e30f;
  case 0xb:
    cVar3 = FUN_1405515a0(param_3);
    if (cVar3 != '\0') goto LAB_14097eccd;
    cVar3 = FUN_1409817f0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x98);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409818c0(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x140);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140981990(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x148);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140981a60(param_3);
    if (cVar3 == '\0') {
      cVar3 = FUN_140981b30(param_3);
      if (cVar3 == '\0') break;
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "silentClose";
        *puVar6 = hx::CMemberFunction0::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_140975220;
        goto LAB_14097fda6;
      }
    }
    else {
      if ((int)(DWORD)DAT_1421bb758 < 0x40) {
        plVar5 = *(longlong **)((ulonglong)DAT_1421bb758._4_4_ + 0xff00000000);
      }
      else {
        plVar5 = TlsGetValue((DWORD)DAT_1421bb758);
      }
      puVar6 = (undefined8 *)plVar5[1];
      if ((ulonglong)plVar5[2] < (longlong)puVar6 + 0x24U) {
        puVar6 = (undefined8 *)(**(code **)(*plVar5 + 8))(plVar5,0x20,0x800000);
      }
      else {
        plVar5[1] = (longlong)puVar6 + 0x24U;
        *(undefined4 *)((longlong)puVar6 + -4) = 0x800020;
      }
      (**(code **)(*plVar5 + 0x18))(plVar5,puVar6,0,1);
      if (puVar6 != (undefined8 *)0x0) {
        *(undefined8 **)param_2 = puVar6;
        puVar6[3] = "replyToPing";
        *puVar6 = hx::CMemberFunction2::vftable;
        puVar6[1] = param_1;
        puVar6[2] = FUN_140965f70;
        goto LAB_14097fda6;
      }
    }
LAB_14097e30f:
    param_2[0] = 0;
    param_2[1] = 0;
    goto LAB_14097fda6;
  case 0xc:
    cVar3 = FUN_140981c00(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 8);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140981ce0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x18);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140981dc0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0xe8);
      param_2[3] = *(int *)(param_1 + 0xe0);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_140981ea0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x1a0);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140981f80(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x1a8);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140982060(param_3);
    if ((cVar3 != '\0') && (param_4 == 2)) {
      cVar3 = FUN_1403fad90();
      if (cVar3 != '\0') {
        *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0x168);
        param_2[2] = 5;
        return param_2;
      }
      goto LAB_14097e8e4;
    }
    cVar3 = FUN_140982140(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(local_res18,"set_delegate",param_1,FUN_14061e7f0);
      *(undefined8 *)param_2 = local_res18[0];
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140982220(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_128,"get_receiver",param_1,&LAB_140407740);
      *(undefined8 *)param_2 = local_128;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140982300(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_120,"set_receiver",param_1,FUN_140945f50);
      *(undefined8 *)param_2 = local_120;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409823e0(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_118,"loadComplete",param_1,FUN_140965bd0);
      *(undefined8 *)param_2 = local_118;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409824c0(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_110,"disconnected",param_1,FUN_140966390);
      *(undefined8 *)param_2 = local_110;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409825a0(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_108,"dataReceived",param_1,FUN_14097ca60);
      *(undefined8 *)param_2 = local_108;
      goto LAB_14097fda6;
    }
    break;
  case 0xd:
    cVar3 = FUN_140982680(param_3);
    if ((cVar3 != '\0') && (param_4 == 2)) {
      lVar2 = *(longlong *)(param_1 + 0x90);
      param_2[2] = 5;
      *(bool *)param_2 = lVar2 != 0;
      return param_2;
    }
    cVar3 = FUN_140982770(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x70);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140982860(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x118);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140982950(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0x168);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_140982a40(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_100,"get_connected",param_1,&LAB_14092c9f0);
      *(undefined8 *)param_2 = local_100;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140982b30(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_f8,"securityError",param_1,FUN_140930ff0);
      *(undefined8 *)param_2 = local_f8;
      goto LAB_14097fda6;
    }
    break;
  case 0xe:
    cVar3 = FUN_140982c20(param_3);
    if ((cVar3 != '\0') && (param_4 == 2)) {
      if ((*(int *)(param_1 + 0x138) != 0x1bb) ||
         (iVar4 = *(int *)(param_1 + 0x13c), *(int *)(param_1 + 0x13c) < 1)) {
        iVar4 = *(int *)(param_1 + 0x138);
      }
      *param_2 = iVar4;
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140982d20(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_f0,"get_inviteCode",param_1,FUN_14092c8e0);
      *(undefined8 *)param_2 = local_f0;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140982e20(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_e8,"packetReceived",param_1,FUN_140963990);
      *(undefined8 *)param_2 = local_e8;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140982f20(param_3);
    if (cVar3 != '\0') {
      FUN_1400305c0(&local_e0,"writeWithNonce",param_1,FUN_140964470);
      *(undefined8 *)param_2 = local_e0;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983020(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_d8,"loadingPercent",param_1,FUN_140964630);
      *(undefined8 *)param_2 = local_d8;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983120(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_d0,"nextNonceProof",param_1,FUN_140965120);
      *(undefined8 *)param_2 = local_d0;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983220(param_3);
    if (cVar3 != '\0') {
      FUN_140030a10(&local_c8,"writeUdpPacket",param_1,FUN_14096de90);
      *(undefined8 *)param_2 = local_c8;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983320(param_3);
    if (cVar3 != '\0') {
      FUN_140030eb0(&local_c0,"buildUdpPacket",param_1,FUN_14096e270);
      *(undefined8 *)param_2 = local_c0;
      goto LAB_14097fda6;
    }
    break;
  case 0xf:
    cVar3 = FUN_140983420(param_3);
    if ((cVar3 != '\0') && (param_4 == 2)) {
LAB_14097f67a:
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 400);
      param_2[3] = *(int *)(param_1 + 0x188);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_140983520(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0xbc);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_14054e280(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x13c);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140983620(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x178);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983720(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x184);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140983820(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_b8,"onSocketConnect",param_1,FUN_14092cce0);
      *(undefined8 *)param_2 = local_b8;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_14054e580(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_b0,"connectionError",param_1,FUN_140938460);
      *(undefined8 *)param_2 = local_b0;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983920(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_a8,"outputBandwidth",param_1,FUN_14093ab30);
      *(undefined8 *)param_2 = local_a8;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983a20(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_a0,"everythingReady",param_1,FUN_140016300);
      *(undefined8 *)param_2 = local_a0;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983b20(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_98,"sendClearPacket",param_1,FUN_140970000);
      *(undefined8 *)param_2 = local_98;
      goto LAB_14097fda6;
    }
    break;
  case 0x10:
    cVar3 = FUN_140983c20(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x78);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140983d30(param_3);
    if (cVar3 != '\0') goto LAB_14097f67a;
    cVar3 = FUN_140983e40(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_90,"cancelConnection",param_1,FUN_1409336c0);
      *(undefined8 *)param_2 = local_90;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140983f50(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_88,"get_udpAvailable",param_1,FUN_14093ae60);
      *(undefined8 *)param_2 = local_88;
      goto LAB_14097fda6;
    }
    break;
  case 0x11:
    cVar3 = FUN_140984060(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x28);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140984180(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x3c);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_1407ab8f0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0xa0);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409842a0(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x16c);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_1409843c0(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_80,"restoreBackupData",param_1,FUN_140016300);
      *(undefined8 *)param_2 = local_80;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409844e0(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_78,"get_hasInviteCode",param_1,&LAB_14092cc10);
      *(undefined8 *)param_2 = local_78;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140984600(param_3);
    if (cVar3 != '\0') {
      FUN_140030a10(&local_70,"writeClearWithUdp",param_1,FUN_14096f9e0);
      *(undefined8 *)param_2 = local_70;
      goto LAB_14097fda6;
    }
    break;
  case 0x12:
    cVar3 = FUN_1407acc50(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0xa8);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140984720(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0xb8);
      param_2[2] = 3;
      return param_2;
    }
    cVar3 = FUN_140984850(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_68,"get_connectionPort",param_1,FUN_140945e80);
      *(undefined8 *)param_2 = local_68;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140984980(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_60,"preloadingComplete",param_1,FUN_140964660);
      *(undefined8 *)param_2 = local_60;
      goto LAB_14097fda6;
    }
    break;
  case 0x13:
    cVar3 = FUN_140984ab0(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0x2c);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_140984bf0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0x100);
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140984d30(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0x170);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_140984e70(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_58,"get_connectionToken",param_1,FUN_14092c930);
      *(undefined8 *)param_2 = local_58;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140984fb0(param_3);
    if (cVar3 != '\0') {
      FUN_140030210(&local_50,"packetReceivedClear",param_1,FUN_1409662f0);
      *(undefined8 *)param_2 = local_50;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_1409850f0(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_48,"processIncomingData",param_1,FUN_14097ca30);
      *(undefined8 *)param_2 = local_48;
      goto LAB_14097fda6;
    }
    break;
  case 0x14:
    cVar3 = FUN_140985230(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0xc2);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_140985370(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0xd0);
      param_2[3] = *(int *)(param_1 + 200);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_1409854b0(param_3);
    if (cVar3 != '\0') {
      *(undefined8 *)param_2 = *(undefined8 *)(param_1 + 0xf8);
      param_2[3] = *(int *)(param_1 + 0xf0);
      param_2[2] = 1;
      return param_2;
    }
    cVar3 = FUN_1409855f0(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_40,"stopCancelConnection",param_1,FUN_14092cc70);
      *(undefined8 *)param_2 = local_40;
      goto LAB_14097fda6;
    }
    cVar3 = FUN_140985730(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_38,"connectionCantResume",param_1,FUN_14096dc00);
      *(undefined8 *)param_2 = local_38;
      goto LAB_14097fda6;
    }
    break;
  case 0x15:
    cVar3 = FUN_140985870(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0xc1);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_1409859c0(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0xd8);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_140985b10(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(&local_30,"tryToResumeConnection",param_1,FUN_14096db20);
      *(undefined8 *)param_2 = local_30;
      goto LAB_14097fda6;
    }
    break;
  case 0x16:
    cVar3 = FUN_140985c60(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0xb0);
      param_2[2] = 3;
      return param_2;
    }
    break;
  case 0x17:
    cVar3 = FUN_140985dc0(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0xb4);
      param_2[2] = 3;
      return param_2;
    }
    break;
  case 0x18:
    cVar3 = FUN_140985f30(param_3);
    if (cVar3 != '\0') {
      *(undefined1 *)param_2 = *(undefined1 *)(param_1 + 0x2d);
      param_2[2] = 5;
      return param_2;
    }
    cVar3 = FUN_1409860b0(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0xc4);
      param_2[2] = 3;
      return param_2;
    }
    break;
  case 0x1a:
    cVar3 = FUN_140986230(param_3);
    if (cVar3 != '\0') {
      *param_2 = *(int *)(param_1 + 0x180);
      param_2[2] = 3;
      return param_2;
    }
    break;
  case 0x23:
    cVar3 = FUN_1409863c0(param_3);
    if (cVar3 != '\0') {
      FUN_14002fe90(local_28,"backupAndResetCurrentConnectionData",param_1,FUN_14092cbe0);
      *(undefined8 *)param_2 = local_28[0];
      goto LAB_14097fda6;
    }
  }
  param_2[0] = 0;
  param_2[1] = 0;
LAB_14097fda6:
  param_2[2] = 0;
  return param_2;
}

