# Ghidra EXACT C Formulas — FUN_1403df080 (M2XC encrypt)

> Source file: `deep_FUN_1403df080.txt` (1698 lines)
> Notes file: `FUN_1403df080_notes.txt` (45 lines)
> Variable mapping: uStackX_20 = H1, uStack_2a0 = H2, uStack_2a8 = len(DATA), *param_3 = first4(KEY), param_3 = KEY string pointer, param_2 = DATA string pointer

---

## Section 1: PRNG + Time + H1 (lines 295-391)

```c
// LINE 295-303: PRNG triple call+combination
uVar3 = FUN_141c02aa0();            // PRNG call 1
uVar4 = FUN_141c02aa0();            // PRNG call 2
bVar2 = FUN_141c02aa0();            // PRNG call 3
dVar31 = (double)(((uint)bVar2 << 0xc | uVar4 & 0xfff) << 0xc | uVar3 & 0xfff) *
         2.3283064365386963e-10 * 2147483647.0;

// LINES 305-315: clamp double→uint
if ((dVar31 < -2147483647.0) || (2147483647.0 < dVar31)) {
    uVar25 = (ulonglong)dVar31;
} else {
    uVar25 = (ulonglong)(uint)(int)dVar31;
}

// LINES 317-319: GetSystemTime + FileTime (first)
GetSystemTime(auStack_138);
SystemTimeToFileTime(auStack_138, &uStack_2c8);

// LINES 367-371: time_ms = ((FileTime + EPOCH) / 10_000_000) + milliseconds*0.001 → seconds
dVar31 = ((double)(int)((CONCAT44(uStack_2c4, uStack_2c8) + 0xfe624e212ac18000U) / 10000000) +
          (double)uStack_12a * 0.001) * 1000.0 * 0.001;
puVar12[1] = dVar31;

// LINES 373-385: * 1000, clamp double→int → time_ms_integer
dVar31 = dVar31 * 1000.0;
if ((dVar31 < -2147483647.0) || (2147483647.0 < dVar31)) {
    iVar5 = (int)(longlong)dVar31;
} else {
    iVar5 = (int)dVar31;
}

// LINE 387: H1 = FUN_1404054c0(iVar5, uVar25 & 0xffffffff)  =  mix(time, PRNG)
uVar4 = func_0x0001404054c0(iVar5, uVar25 & 0xffffffff);
iRam00000001421b8aa0 = iRam00000001421b8aa0 + 1;

// LINE 391: store H1
uStackX_20 = uVar4;   // ← H1 permanently stored here throughout entire function
```

**Variables:**
| Ghidra name | Semantic | Type |
|---|---|---|
| `uVar3,uVar4,bVar2` | 3 PRNG calls (linear congruential?) | `uint` |
| `iVar5` | time_ms in integer milliseconds | `int` |
| `uVar25 & 0xffffffff` | PRNG result masked to 32-bit | `uint` |
| `uStackX_20` | **H1** (first hash, stored at `[RSP+0x308]`) | `uint` |
| `uStack_2c8, uStack_2c4` | FileTime low/high parts | `uint` |
| `uStack_12a` | milliseconds field from SYSTEMTIME | `ushort` |

---

## Section 2: PRNG + Time + H2 + fmix mixing (lines 392-491)

```c
// LINES 393-413: PRNG (same pattern as Section 1, fresh random values)
uVar6 = FUN_141c02aa0();
uVar7 = FUN_141c02aa0();
bVar2 = FUN_141c02aa0();
dVar31 = (double)(((uint)bVar2 << 0xc | uVar7 & 0xfff) << 0xc | uVar6 & 0xfff) *
         2.3283064365386963e-10 * 2147483647.0;
if ((dVar31 < -2147483647.0) || (2147483647.0 < dVar31)) {
    uVar25 = (ulonglong)dVar31;
} else {
    uVar25 = (ulonglong)(uint)(int)dVar31;
}

// LINES 415-417: GetSystemTime + FileTime (second)
GetSystemTime(auStack_128);
SystemTimeToFileTime(auStack_128, &uStack_2b8);

// LINES 461-479: time_ms computation + clamp (same pattern)
dVar31 = ((double)(int)((CONCAT44(uStack_2b4, uStack_2b8) + 0xfe624e212ac18000U) / 10000000) +
          (double)uStack_11a * 0.001) * 1000.0 * 0.001;
puVar12[1] = dVar31;
dVar31 = dVar31 * 1000.0;
if ((dVar31 < -2147483647.0) || (2147483647.0 < dVar31)) {
    iVar5 = (int)(longlong)dVar31;
} else {
    iVar5 = (int)dVar31;
}

// LINE 481: H2_raw = FUN_1404054c0(time2, rand2)
uVar6 = func_0x0001404054c0(iVar5, uVar25 & 0xffffffff);

// LINES 483-489: H2 ^= fmix(first4(KEY) ^ H1 ^ len(DATA))
uVar4 = *param_3 ^ uVar4 ^ uStack_2a8;   // first4(KEY) ^ H1 ^ len(DATA)
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;   // fmix round 1
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;   // fmix round 2
uVar6 = uVar6 ^ uVar4 ^ uVar4 >> 0x10;          // H2 = H2_raw ^ fmix ^ (fmix >> 16)

// LINE 491: store H2
uStack_2a0 = CONCAT44(uStack_2a0._4_4_, uVar6);
auStack_280[0] = auStack_280[0] & 0xffffff00;
auStack_280[1] = 0;
uStack_2b0 = uVar6;

// ===== KS1 assembly (lines 553-573, inside main loop body) =====
// Precondition: uVar4 = uStackX_20 (= H1) at line 553

// LINE 557: append H1 (4 bytes LE)
FUN_140406ce0(lStack_1a8, uStackX_20);

// LINE 559-561: append H2 (4 bytes LE)
uVar6 = (uint)uStack_2a0;
FUN_140406ce0(lStack_1a8, uStack_2a0 & 0xffffffff);

// LINES 563-567: append fmix(H1 ^ 0x12345678)
uVar4 = ((uVar4 ^ 0x12345678) >> 0x10 ^ uVar4 ^ 0x12345678) * 0x45d9f3b;
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
FUN_140406ce0(lStack_1a8, uVar4 ^ uVar4 >> 0x10);   // fmix(H1 ^ 0x12345678)

// LINES 569-573: append fmix(H2 ^ 0x87654321)
uVar4 = ((uVar6 ^ 0x87654321) >> 0x10 ^ uVar6 ^ 0x87654321) * 0x45d9f3b;
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
FUN_140406ce0(lStack_1a8, uVar4 ^ uVar4 >> 0x10);   // fmix(H2 ^ 0x87654321)
```

**KS1 layout (16 bytes):** `H1 | H2 | fmix(H1 ^ 0x12345678) | fmix(H2 ^ 0x87654321)`

**Variables:**
| Ghidra name | Semantic | Type |
|---|---|---|
| `uStack_2a0` | **H2** (second hash) | `ulonglong` |
| `uStack_2b0` | H2 low dword alias | `uint` |
| `uStack_2a8` | `*(uint *)(lVar24 + 8)` = len(DATA) | `uint` |
| `*param_3` | first 4 bytes of KEY (dereferenced as `uint*`) | `uint` |

---

## Section 3: Pass A state init + keystream (lines 575-731)

### Pre-keystream loop (lines 585-599) — iterates over KS1 bytes

```c
// LINES 585-599: Process KS1 through fmix to produce initial uVar4
while (uVar6 = (uint)plVar15, (int)uVar6 < *(int *)(alStack_1e8[0] + 8)) {
    uVar7 = FUN_140406270(alStack_1e8[0]);     // read next byte from KS1 string
    uVar4 = uVar7 ^ uVar4 ^ uVar6;              // byte ^ accumulator ^ counter
    uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
    uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
    uVar4 = uVar4 >> 0x10 ^ uVar4;
    plVar15 = (longlong *)(ulonglong)(uVar6 + 1);   // counter++
}
uRam00000001421b8a8c = uVar4;
```
Note: This loop reads/processes KS1 bytes but does NOT modify w0-w3 state. It produces a final `uVar4` stored to a global/tls variable, then the state init uses it indirectly via the mul/add constants.

### Pass A state init (lines 611-641) — 4 fmix calls

```c
// LINES 611-617: w0 = fmix( len(DATA) ^ H1 ^ 0x243f6a88 )
uVar4 = *(uint *)(lVar24 + 8) ^ uStackX_20 ^ 0x243f6a88;   // = len(DATA) ^ H1 ^ 0x243f6a88
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uVar7 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uVar7 = uVar7 >> 0x10 ^ uVar7;                               // ◄ w0 stored in uVar7

// LINES 619-623: w1 = fmix( H2 ^ 0x85a308d3 )
uVar4 = (((uint)uStack_2a0 ^ 0x85a308d3) >> 0x10 ^ (uint)uStack_2a0 ^ 0x85a308d3) * 0x45d9f3b;
uStack_2b8 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uStack_2b8 = uStack_2b8 >> 0x10 ^ uStack_2b8;                // ◄ w1 stored in uStack_2b8

// LINES 625-633: w2 = fmix( first4(KEY) ^ rotl(H1,7) ^ 0x13198a2e )
uVar4 = *param_3;
uVar6 = uVar4 ^ (uStackX_20 >> 0x19 | uStackX_20 << 7) ^ 0x13198a2e;   // rotl(H1,7)
uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uStack_2c8 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uStack_2c8 = uStack_2c8 >> 0x10 ^ uStack_2c8;                   // ◄ w2 stored in uStack_2c8

// LINES 635-641: w3 = fmix( rotl(H2,11) ^ 0x3707344 )
uVar6 = ((uint)uStack_2a0 >> 0x15 | (uint)uStack_2a0 << 0xb) ^ 0x3707344;   // rotl(H2,11)
uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uVar6 = uVar6 >> 0x10 ^ uVar6;                                     // ◄ w3 stored in uVar6
```

**State mapping after init:**
| State var | Ghidra variable | Init formula |
|---|---|---|
| `w0` | `uVar7` | `fmix(len(DATA) ^ H1 ^ 0x243f6a88)` |
| `w1` | `uStack_2b8` | `fmix(H2 ^ 0x85a308d3)` |
| `w2` | `uStack_2c8` | `fmix(first4(KEY) ^ rotl(H1,7) ^ 0x13198a2e)` |
| `w3` | `uVar6` | `fmix(rotl(H2,11) ^ 0x3707344)` |

### Pass A keystream loop (lines 643-731)

```c
// LINE 643: loop condition = KEYS_BYTEINDEX (uVar4 = *param_3 = len(KEY))
if (0 < (int)uVar4) {

    // LINE 645: accumulator init
    iVar5 = (uint)uStack_2a0 + uStackX_20;   // = H2 + H1

    // LINE 647: counter init
    uStack_2c0 = 0;

    // LINES 649-654: declare loop pointers
    plVar15 = plVar18;   // index counter (i)
    plVar26 = plVar18;   // used for KEY byte index
    plVar29 = plVar18;   // used for KEY byte pointer arithmetic

    do {
        iVar23 = (int)plVar15;                     // i = loop index
        uVar28 = (uint)plVar26;                    // (redundant, = i)
        uVar8 = uVar3;                             // accumulator c (starts at uVar3=0)

        // LINES 663-677: KEY byte fetch via FUN_14002f450 virtual dispatch
        if (((-1 < iVar23) && (iVar23 < (int)uVar4)) &&
           (plVar15 = (longlong *)FUN_14002f450(
                        *(undefined1 *)(*(longlong *)(param_3 + 2) + (longlong)plVar29)),
            uVar28 = uStack_2c0, plVar15 != (longlong *)0x0)) {
            uVar8 = (**(code **)(*plVar15 + 0x38))(plVar15);   // virtual call: get byte
            uVar28 = uStack_2c0;
        }

        // LINE 679: TEA update 1 — w0 update
        //   w0 = w0 + ((w3 << 8 | w3 >> 29) + c + i + KEY_byte)
        //   Then fmix(w0) → new w0
        uVar7 = (uVar6 >> 0x1d | uVar6 * 8) + uVar8 + iVar23 + uVar7;   // w0 += rotl(w3,8) + c + i + KEY_byte
        uVar4 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uVar7 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uVar7 = uVar7 >> 0x10 ^ uVar7;                                     // w0 = fmix(w0)

        // LINE 687-689: TEA update 2 — w1 update
        //   w1 = w1 ^ rotl(c + i + w0, 7)
        //   Then fmix(w1) → new w1
        uVar4 = uVar8 + iVar23 + uVar7;                                     // c + i + w0
        uStack_2b8 = (uVar4 >> 0x19 | uVar4 * 0x80) ^ uStack_2b8;          // w1 ^= rotl(val, 7)
        uVar4 = (uStack_2b8 >> 0x10 ^ uStack_2b8) * 0x45d9f3b;
        uStack_2b8 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uStack_2b8 = uStack_2b8 >> 0x10 ^ uStack_2b8;                      // w1 = fmix(w1)

        // LINE 697-705: TEA update 3 — w2 update
        //   w2 = w2 + rotl((c ^ w1), 11) + counter
        //   Then fmix(w2) → new w2
        uVar4 = uStack_2c8 + ((uVar8 ^ uStack_2b8) >> 0x15 | (uVar8 ^ uStack_2b8) << 0xb) + uVar28;
        uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uStack_2c8 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uStack_2c8 = uStack_2c8 >> 0x10 ^ uStack_2c8;                      // w2 = fmix(w2)

        // LINE 707-715: TEA update 4 — w3 update
        //   w3 = w3 ^ (rotl(c + H2 + H1, 15) ^ w0 ^ w2)
        //   Then fmix(w3) → new w3
        uVar8 = uVar8 + iVar5;                                              // c + (H2+H1)
        uVar4 = (uVar8 >> 0xf | uVar8 * 0x20000) ^ uVar6 ^ uStack_2c8;     // rotl(val,15) ^ w3 ^ w2
        uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uVar6 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uVar6 = uVar6 >> 0x10 ^ uVar6;                                      // w3 = fmix(w3)

        // LINES 717-723: counter increment, accumulator update
        plVar15 = (longlong *)(ulonglong)(iVar23 + 1U);   // i++
        uStack_2c0 = uVar28 + 0x45d9f3b;                  // c += 0x45d9f3b  (TEA delta)
        plVar26 = (longlong *)(ulonglong)uStack_2c0;
        plVar29 = (longlong *)((longlong)plVar29 + 1);    // KEY byte pointer++
        uVar4 = *param_3;                                  // re-read len(KEY)
        lVar24 = uStack_290;

    } while ((int)(iVar23 + 1U) < (int)uVar4);   // loop: i < len(KEY)
}
```

**Keystream loop variables:**

| Ghidra | Role | Derivation |
|---|---|---|
| `iVar23` | loop index `i` | 0, 1, 2, ... |
| `uStack_2c0` | accumulator `c` | starts 0, += 0x45d9f3b each iter |
| `uVar8` | KEY byte value `k[i]` | via virtual dispatch on param_3 |
| `iVar5` | constant `H2 + H1` | computed once before loop |
| `uVar7` | `w0` | fmix of TEA sum |
| `uStack_2b8` | `w1` | fmix of XOR |
| `uStack_2c8` | `w2` | fmix of sum |
| `uVar6` | `w3` | fmix of XOR |

**TEA update formulas (pseudocode):**
```
w0 = fmix(w0 + rotl(w3, 8) + c + i + k[i])
w1 = fmix(w1 ^ rotl(c + i + w0, 7))
w2 = fmix(w2 + rotl(c ^ w1, 11) + c_prev)
w3 = fmix(w3 ^ rotl(c + H2_plus_H1, 15) ^ w2)    [uses PREVIOUS w2 before update]
c += 0x45d9f3b
```

---

## Section 4: Pass A swfinalize (lines 733-755)

```c
// LINES 733-737: w0f = fmix(w0 ^ 0xa5a5a5a5)
uVar4 = ((uVar7 ^ 0xa5a5a5a5) >> 0x10 ^ uVar7 ^ 0xa5a5a5a5) * 0x45d9f3b;
uVar7 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uVar8 = uVar7 >> 0x10 ^ uVar7;                        // ◄ w0f = uVar8

// LINES 739-743: w1f = fmix(w1 + 0x3c6ef372)
uVar4 = (uStack_2b8 + 0x3c6ef372 >> 0x10 ^ uStack_2b8 + 0x3c6ef372) * 0x45d9f3b;
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uVar28 = uVar4 >> 0x10 ^ uVar4;                       // ◄ w1f = uVar28

// LINES 745-749: w2f = fmix(rotl(w0f, 13) ^ w2)
uVar7 = (uVar7 >> 0x13 | uVar8 << 0xd) ^ uStack_2c8; // rotl(w0f, 13) ^ w2
uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
// w2f = uVar7 >> 0x10 ^ uVar7   (stored as "raw" fmix, finalize happens at later use)

// LINES 751-755: w3f = fmix(rotl(w1f, 9) + w3)
uVar6 = (uVar28 << 9 | uVar4 >> 0x17) + uVar6;       // rotl(w1f, 9) + w3
uVar4 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
// w3f = uVar4 >> 0x10 ^ uVar4  (same pattern as w2f)
```

**Finalized state written to SW structure (lines 757-769):**
```c
// LINES 757-769: push final w0f/w1f/w2f/w3f into SW state
plVar15 = (longlong *)FUN_1400433c0(auStack_110, 4);
uVar14 = uStack_288;
lVar11 = *plVar15;

*(uint **)(lVar11 + 0x18) = uVar8;                             // w0f
*(uint *)(*(longlong *)(lVar11 + 0x18) + 4) = uVar28;          // w1f
*(uint *)(*(longlong *)(lVar11 + 0x18) + 8) = uVar7 >> 0x10 ^ uVar7;   // w2f = fmix(rotl(w0f,13)^w2)
*(uint *)(*(longlong *)(lVar11 + 0x18) + 0xc) = uVar4 >> 0x10 ^ uVar4; // w3f = fmix(rotl(w1f,9)+w3)
```

| Finalized value | Expression |
|---|---|
| `w0f` (uVar8) | `fmix(w0 ^ 0xa5a5a5a5)` |
| `w1f` (uVar28) | `fmix(w1 + 0x3c6ef372)` |
| `w2f` (written) | `fmix(rotl(w0f, 13) ^ w2)` |
| `w3f` (written) | `fmix(rotl(w1f, 9) + w3)` |

**CRITICAL:** `w0f/w1f` use the `raw` variable (`uVar7`/`uVar4` pre-final XOR), while `w2f/w3f` use the finalized value (post `>> 16 ^` at write time). The write at line 767 uses `uVar7 >> 0x10 ^ uVar7` (finalizing at store time), and line 769 uses `uVar4 >> 0x10 ^ uVar4` (finalizing at store time).

---

## Section 5: Pass A emit loop (lines 797-977)

```c
// LINE 797: loop condition = len(DATA)
if (0 < *(int *)(lVar24 + 8)) {
    do {
        // LINE 801: read next DATA byte
        auStack_298[0] = FUN_140406270(lVar24);    // DATA[i], stored in auStack_298[0]

        // LINES 803-837: read w0..w3 from SW state structure
        uVar4 = *(uint *)(lVar11 + 0x10);           // element count (0-4)
        piVar20 = *(int **)(lVar11 + 0x18);         // pointer to state array

        iVar5 = 0;
        if (uVar4 != 0) { iVar5 = *piVar20; }                    // w0[i=0]

        plVar26 = plVar18;
        if (1 < uVar4) { plVar26 = (longlong *)(ulonglong)(uint)piVar20[1]; }  // w1[i=1]

        plVar29 = plVar18;
        if (2 < uVar4) { plVar29 = (longlong *)(ulonglong)(uint)piVar20[2]; }  // w2[i=2]

        plVar27 = plVar18;
        if (3 < uVar4) { plVar27 = (longlong *)(ulonglong)(uint)piVar20[3]; }  // w3[i=3]

        // LINES 839-847: fmix(rotl(w1,5) + w0 + delta + i) → new w0_temp
        uVar6 = ((uint)((ulonglong)plVar26 >> 0x1b) | (uint)plVar26 << 5) + iVar5 + -0x61c88647 +
                (uint)plVar15;
        uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
        uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
        uStack_2b8 = uVar6 >> 0x10 ^ uVar6;           // ◄ TEA sum result

        // LINES 849-857: fmix((rotl(w2,7) ^ w1 ^ w0_temp)) → new w3_temp
        uVar7 = ((uint)((ulonglong)plVar29 >> 0x19) | (int)plVar29 << 7) ^ (uint)plVar26 ^
                uStack_2b8;
        uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uStack_2c8 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uStack_2c8 = uStack_2c8 >> 0x10 ^ uStack_2c8;  // ◄ fmix result

        // LINES 859-867: fmix(rotl(w3,11) + w2 + w3_temp) → new w4_temp
        uVar7 = ((uint)((ulonglong)plVar27 >> 0x15) | (uint)plVar27 << 0xb) + (int)plVar29 +
                uStack_2c8;
        uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uVar28 = uVar7 >> 0x10 ^ uVar7;                 // ◄ fmix result

        // LINES 869-875: fmix(rotl(w0_temp,13) ^ w3 ^ w4_temp ^ i) → final output word
        uVar6 = (uVar6 >> 0x13 | uStack_2b8 << 0xd) ^ (uint)plVar27 ^ uVar28 ^ (uint)plVar15;
        uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
        uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
        uVar6 = uVar6 >> 0x10 ^ uVar6;                  // ◄ uStack_2b0 = hash_acc

        uStack_2b0 = uVar6;                              // save hash_acc

        // LINES 879-937: write back updated state
        // ... (state growth + element storage, same pattern as finalize)
        **(uint **)(lVar11 + 0x18) = uStack_2b8;        // w0' = uStack_2b8
        *(uint *)(*(longlong *)(lVar11 + 0x18) + 4) = uStack_2c8;  // w1' = uStack_2c8
        *(uint *)(*(longlong *)(lVar11 + 0x18) + 8) = uVar28;      // w2' = uVar28
        *(uint *)(*(longlong *)(lVar11 + 0x18) + 0xc) = uVar6;     // w3' = uVar6

        // LINES 937-941: compute rotl components for output
        uVar30 = uStack_2c8 >> 0x1d;                    // w1 >> 29
        uVar4 = uStack_2c8 * 8;                          // w1 << 3
        uStack_290 = CONCAT44(uStack_290._4_4_, uVar7 >> 0x17 | uVar28 << 9);  // rotl(w3,9) mixed
        uVar7 = uStack_2b0 << 0x11;                      // hash_acc << 17

        // LINES 945-957: read output byte from state (indexed by counter)
        uVar28 = (int)uStack_2c0 >> 2 & 3;               // (c >> 2) & 3
        if (uVar28 < *(uint *)(lVar11 + 0x10)) {
            uStack_2c8 = *(uint *)(*(longlong *)(lVar11 + 0x18) + (ulonglong)uVar28 * 4);
        } else {
            uStack_2c8 = 0;
        }

        // LINES 959-971: output byte computation
        FUN_1404073c0(lStack_1d8, *(int *)(lStack_1d8 + 0x1c) + 1);   // grow output string
        *(int *)(lStack_1d8 + 0x1c) = *(int *)(lStack_1d8 + 0x1c) + 1;
        pcVar17 = (char *)FUN_1400281e0(*(undefined8 *)(lStack_1d8 + 0x10));

        sVar22 = (sbyte)((uVar8 & 3) << 3);              // (c & 3) * 8 = shift amount

        *pcVar17 = ((byte)(((uVar6 >> 0xf | uVar7) ^      // rotl(hash_acc,17) ^
                            (uint)uStack_290 ^              // rotl(w3,9) ^
                            (uVar30 | uVar4) ^              // rotl(w1,3) ^
                            uStack_2b8) >> sVar22) ^        // w0 >> shift
                    (byte)auStack_298[0]) +                 // XOR DATA[i]
                   (char)(uStack_2c8 >> sVar22) +           // + state_byte >> shift
                   (char)uStackX_20 +                       // + H1
                   (char)uStack_2c0;                        // + c

        uStack_2c0 = uStack_2c0 + 1;                        // c++
        plVar15 = (longlong *)(ulonglong)uStack_2c0;

    } while ((int)uStack_2c0 < *(int *)(lVar24 + 8));       // loop: c < len(DATA)
}
```

**Emit loop key details:**
| Component | Expression |
|---|---|
| TEA `w0` | `rotl(w1,5) + w0 + (-0x61c88647) + c` ... then fmix |
| TEA `w1` | `rotl(w2,7) ^ w1 ^ new_w0` ... then fmix |
| TEA `w2` | `rotl(w3,11) + w2 + new_w1` ... then fmix |
| TEA `w3` | `rotl(new_w0,13) ^ w3 ^ new_w2 ^ c` ... then fmix |
| **hash_acc** | `fmix(w3_from_TEA)` — computed FRESH each iteration, NOT chained |
| Output byte | `((rotl(hash_acc,17) ^ rotl(w3,9) ^ rotl(w1,3) ^ w0) >> shift) ^ DATA[i] + (state_byte>>shift) + H1 + c` |

**IMPORTANT:** The TEA update formula here is **different** from Section 3's keystream loop. Section 3 uses `c + i + KEY_byte` patterns; this emit loop uses pure TEA (rotl/sum/XOR on state words with delta = -0x61c88647 = 0x9e3779b9). The `hash_acc` is the final `w3` of the TEA round, freshly computed each iteration.

---

## Section 6: Pass A transform2 (lines 1015-1035)

```c
// LINE 1013-1014: loop condition, prev init
plVar15 = plVar18;                    // counter/prev = 0
uVar4 = (uint)uStack_2a0;            // uVar4 = H2 & 0xffffffff (used as "prev" base)

if (0 < *(int *)(lStack_1d8 + 8)) {  // if len(round1) > 0
    do {
        // LINE 1017: read round1 byte
        uVar7 = FUN_140406270(lStack_1d8);      // byte from round1 = round1[i]

        // LINE 1019-1023: transform formula
        uVar28 = (uint)plVar15;                  // i = counter
        uVar4 = uVar7 ^ (uVar6 >> (sbyte)((uVar28 & 3) << 3)) + (uVar4 & 0xff) + uVar28 ^
                uVar4 & 0xff;

        // LINES 1025-1031: append byte to round2 output
        FUN_1404073c0(lVar24, *(int *)(lVar24 + 0x1c) + 1);
        *(int *)(lVar24 + 0x1c) = *(int *)(lVar24 + 0x1c) + 1;
        puVar16 = (undefined1 *)FUN_1400281e0(*(undefined8 *)(lVar24 + 0x10));
        *puVar16 = (char)uVar4;

        plVar15 = (longlong *)(ulonglong)(uVar28 + 1);   // i++
    } while ((int)(uVar28 + 1) < *(int *)(lStack_1d8 + 8));
}
```

**Transform2 formula (exact C):**
```c
prev = H2;  // uVar4 init = H2
for (i = 0; i < len(round1); i++) {
    byte_in = round1[i];
    // operator precedence: >> is LOW, XOR is HIGH, addition is in-between
    //   XOR has lower precedence than +, so:
    //   uVar4 = byte ^ ((H1 >> ((i&3)*8)) + (prev & 0xff) + i) ^ (prev & 0xff)
    uVar4 = byte_in ^ (H1 >> ((i & 3) << 3)) + (prev & 0xff) + i ^ (prev & 0xff);
    round2[i] = (byte)uVar4;
    prev = uVar4 & 0xff;     // ← stored as (uVar4 & 0xff) for next iteration
}
```

**Key observations:**
- The `prev` variable **is** `uVar4` itself (overwritten each iteration)
- `prev = uVar4 & 0xff` (implicit — `uVar4 & 0xff` is used on the right side)
- `H1` is `uVar6` at line 1019 (saved from uStackX_20 earlier)
- The initial `prev = H2 & 0xff` from line 1011: `uVar4 = (uint)uStack_2a0`
- `uStack_2a0` is the `ulonglong`, but line 1011 is `(uint)uStack_2a0` which takes the low 32 bits

**Operator precedence is CRITICAL:**
```c
// Decompiler parens match: a = b ^ c + d + e ^ f
// Actual C order: a = b ^ ((c + d + e) ^ f)
// So: uVar4 = byte ^ ((H1_shifted + prev_byte + i) ^ prev_byte)
uVar4 = round1[i] ^ ((H1 >> ((i & 3) << 3)) + (prev_byte) + i) ^ (prev_byte);
```

---

## Section 7: Pass B setup + keystream (lines 1039-1203)

### KS2 construction (lines 1039-1081)

```c
// LINES 1039-1043: open empty output string lStack_240
auStack_258[0] = 0;
uStack_254 = 0;
FUN_140407920(&lStack_240, uVar14, auStack_258);

// ... (string init boilerplate)

// LINES 1061-1069: append 5 dwords = 20 bytes fixed header
FUN_140406ce0(lVar11, 0x19731f72);                          // constant
FUN_140406ce0(lVar11, uVar6);                                // H1 (uVar6 = uStackX_20)
FUN_140406ce0(lVar11, uStack_2a0 & 0xffffffff);              // H2
FUN_140406ce0(lVar11, uStack_2a8);                           // len(DATA)
FUN_140406ce0(lVar11, *(undefined4 *)(lVar24 + 8));          // len(round2)

// LINES 1071-1081: append round2 bytes
auStack_250[0] = 0;
uStack_24c = *(undefined4 *)(lVar24 + 8);     // len(round2)
auStack_248[0] = 0;
uStack_244 = 0;
lStack_1d0 = lVar24;                          // lVar24 = round2 string handle
FUN_1404069b0(lVar11, &lStack_1d0, auStack_248, auStack_250);  // concat
```

**KS2 layout (20 + len(round2) bytes):**
```
[0x19731f72][H1][H2][len(DATA)][len(round2)][round2_bytes...]
   4 bytes   4   4      4           4          len(round2)
```

### Pass B state init (lines 1083-1122)

```c
// LINE 1085-1087: compute H1_xor = H1 ^ 0x6a09e667, H2_xor = H2 ^ 0xbb67ae85
uStack_2b0 = uVar6 ^ 0x6a09e667;                              // H1 ^ SHA256_K0
uStack_290 = CONCAT44(uStack_290._4_4_, (uint)uStack_2a0) ^ 0xbb67ae85;  // (..H2) ^ SHA256_K1

// LINES 1089-1095: w0 = fmix( len(KS2) ^ (H1 ^ 0x6a09e667) ^ 0x243f6a88 )
uVar4 = *(uint *)(lVar11 + 8) ^ uStack_2b0 ^ 0x243f6a88;     // len(KS2) ^ H1_xor ^ PI_K0
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uVar7 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uVar7 = uVar7 >> 0x10 ^ uVar7;                                // ◄ w0 = uVar7

// LINES 1097-1101: w1 = fmix( H2 ^ 0x3ec4a656 )
uVar4 = (((uint)uStack_2a0 ^ 0x3ec4a656) >> 0x10 ^ (uint)uStack_2a0 ^ 0x3ec4a656) * 0x45d9f3b;
uStack_2c8 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uStack_2c8 = uStack_2c8 >> 0x10 ^ uStack_2c8;                // ◄ w1 = uStack_2c8

// LINES 1103-1111: w2 = fmix( first4(KEY) ^ rotl(H1_xor,7) ^ 0x13198a2e )
uVar4 = *uStackX_18;
uVar6 = uVar4 ^ (uStack_2b0 >> 0x19 | uStack_2b0 << 7) ^ 0x13198a2e;  // rotl(H1^SHA_K0,7)
uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uStack_2b8 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uStack_2b8 = uStack_2b8 >> 0x10 ^ uStack_2b8;                // ◄ w2 = uStack_2b8

// LINES 1113-1121: w3 = fmix( rotl(H2_xor,11) ^ 0x3707344 )
uVar6 = (((uint)uStack_2a0 ^ 0xbb67ae85) >> 0x15 | ((uint)uStack_2a0 ^ 0xbb67ae85) << 0xb) ^
        0x3707344;                                            // rotl(H2 ^ SHA256_K1, 11)
uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uVar6 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uVar6 = uVar6 >> 0x10 ^ uVar6;                                // ◄ w3 = uVar6

uStackX_18 = (uint *)CONCAT44(uStackX_18._4_4_, uVar6);       // w3 packed into uStackX_18
```

**Pass B state init vs Pass A differences:**

| State | **Pass A** | **Pass B** |
|---|---|---|
| `w0` seed | `len(DATA) ^ H1 ^ 0x243f6a88` | `len(KS2) ^ (H1 ^ 0x6a09e667) ^ 0x243f6a88` |
| `w1` seed | `H2 ^ 0x85a308d3` | `H2 ^ 0x3ec4a656` |
| `w2` seed | `first4(KEY) ^ rotl(H1,7) ^ 0x13198a2e` | `first4(KEY) ^ rotl(H1 ^ 0x6a09e667, 7) ^ 0x13198a2e` |
| `w3` seed | `rotl(H2,11) ^ 0x3707344` | `rotl(H2 ^ 0xbb67ae85, 11) ^ 0x3707344` |

**Pass B uses SHA-256 style constants:** `0x6a09e667`, `0xbb67ae85`, `0x3ec4a656` — these are the first three SHA-256 IV words.

### Pass B keystream loop (lines 1125-1203)

```c
// LINE 1125: loop condition = len(KEY)
if (0 < (int)uVar4) {

    // LINE 1127: accumulator init = H2_xor + H1_xor
    iVar5 = (uint)uStack_290 + uStack_2b0;    // = (H2 ^ 0xbb67ae85) + (H1 ^ 0x6a09e667)

    // LINE 1129: counter init
    uStack_2c0 = 0;

    plVar15 = plVar18;    // KEY byte index

    do {
        iVar23 = (int)plVar18;                 // i = loop index
        uVar6 = uVar3;                         // c accumulator (uVar3 = 0 init)

        // KEY byte fetch (same pattern as Pass A)
        if (((-1 < iVar23) && (iVar23 < (int)uVar4)) &&
           (plVar18 = (longlong *)FUN_14002f450(
                        *(undefined1 *)(*(longlong *)(puVar1 + 2) + (longlong)plVar15)),
            plVar18 != (longlong *)0x0)) {
            uVar6 = (**(code **)(*plVar18 + 0x38))(plVar18);
        }

        // LINE 1151: TEA update 1 — w0
        uVar7 = ((uint)uStackX_18 >> 0x1d | (uint)uStackX_18 * 8) + uVar6 + iVar23 + uVar7;
        uVar4 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uVar7 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uVar7 = uVar7 >> 0x10 ^ uVar7;                            // w0 = fmix(w0)

        // LINE 1159-1167: TEA update 2 — w1
        uVar4 = uVar6 + iVar23 + uVar7;                           // c + i + w0
        uStack_2c8 = (uVar4 >> 0x19 | uVar4 * 0x80) ^ uStack_2c8; // w1 ^= rotl(val,7)
        uVar4 = (uStack_2c8 >> 0x10 ^ uStack_2c8) * 0x45d9f3b;
        uStack_2c8 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uStack_2c8 = uStack_2c8 >> 0x10 ^ uStack_2c8;            // w1 = fmix(w1)

        // LINE 1169-1177: TEA update 3 — w2
        uVar4 = uStack_2b8 + ((uVar6 ^ uStack_2c8) >> 0x15 | (uVar6 ^ uStack_2c8) << 0xb) +
                uStack_2c0;
        uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uStack_2b8 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uStack_2b8 = uStack_2b8 >> 0x10 ^ uStack_2b8;            // w2 = fmix(w2)

        // LINE 1179-1187: TEA update 4 — w3
        uVar6 = uVar6 + iVar5;                                    // c + (H2_xor + H1_xor)
        uVar4 = (uVar6 >> 0xf | uVar6 * 0x20000) ^ (uint)uStackX_18 ^ uStack_2b8;  // rotl(val,15)^w3^w2
        uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uVar6 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
        uVar6 = uVar6 >> 0x10 ^ uVar6;                            // w3 = fmix(w3)

        uStackX_18 = (uint *)CONCAT44(uStackX_18._4_4_, uVar6);   // store w3

        // LINES 1191-1193: increment
        plVar18 = (longlong *)(ulonglong)(iVar23 + 1U);           // i++
        uStack_2c0 = uStack_2c0 + 0x45d9f3b;                     // c += delta
        plVar15 = (longlong *)((longlong)plVar15 + 1);            // KEY ptr++
        uVar4 = *puVar1;                                          // re-read len(KEY)
        lVar11 = lStack_240;

    } while ((int)(iVar23 + 1U) < (int)uVar4);                   // loop: i < len(KEY)
}
```

**Pass B keystream vs Pass A differences:**

| Aspect | Pass A | Pass B |
|---|---|---|
| Loop over | DATA bytes (once, `len(DATA)`) | KEY bytes (once, `len(KEY)`) |
| Acc constant `iVar5` | `H2 + H1` | `(H2 ^ 0xbb67ae85) + (H1 ^ 0x6a09e667)` |
| w0 init | `uVar7` from Pass A init | `uVar7` from Pass B init |
| w1 init | `uStack_2b8` | `uStack_2c8` (swapped!) |
| w2 init | `uStack_2c8` | `uStack_2b8` (swapped!) |
| w3 var name | `uVar6` | `uStackX_18` (upper half packed) |
| KEY pointer | `plVar29 += 1` | `plVar15 += 1` |
| plVar18 reuse | thread-local, not modified | **modified** inside loop! |

**CRITICAL BUG NOTE:** Pass B keystream loop **modifies `plVar18`** (line 1141) inside the KEY byte fetch logic, which is the thread-local/GS register pointer. This is DIFFERENT from Pass A which uses `plVar29` as the KEY pointer and keeps `plVar18` unchanged.

---

## Section 8: Pass B swfinalize (lines 1207-1229)

```c
// LINES 1207-1211: w0f = fmix(w0 ^ 0xa5a5a5a5)
uVar3 = ((uVar7 ^ 0xa5a5a5a5) >> 0x10 ^ uVar7 ^ 0xa5a5a5a5) * 0x45d9f3b;
uVar4 = (uVar3 >> 0x10 ^ uVar3) * 0x45d9f3b;
uVar7 = uVar4 >> 0x10 ^ uVar4;                            // ◄ w0f = uVar7

// LINES 1213-1217: w1f = fmix(w1 + 0x3c6ef372)
uVar3 = (uStack_2c8 + 0x3c6ef372 >> 0x10 ^ uStack_2c8 + 0x3c6ef372) * 0x45d9f3b;
uVar3 = (uVar3 >> 0x10 ^ uVar3) * 0x45d9f3b;
uVar28 = uVar3 >> 0x10 ^ uVar3;                           // ◄ w1f = uVar28

// LINES 1219-1223: w2f = fmix(rotl(w0f, 13) ^ w2)
uVar4 = (uVar4 >> 0x13 | uVar7 << 0xd) ^ uStack_2b8;     // rotl(w0f,13) ^ w2
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
uVar4 = (uVar4 >> 0x10 ^ uVar4) * 0x45d9f3b;
// w2f = uVar4 >> 0x10 ^ uVar4  (finalized at write)

// LINES 1225-1229: w3f = fmix(rotl(w1f, 9) + w3)
uVar6 = (uVar28 << 9 | uVar3 >> 0x17) + uVar6;           // rotl(w1f,9) + w3
uVar3 = (uVar6 >> 0x10 ^ uVar6) * 0x45d9f3b;
uVar3 = (uVar3 >> 0x10 ^ uVar3) * 0x45d9f3b;
// w3f = uVar3 >> 0x10 ^ uVar3  (finalized at write)
```

**Written to SW state (lines 1231-1243):**
```c
plVar18 = (longlong *)FUN_1400433c0(auStack_108, 4);
lVar13 = *plVar18;

**(uint **)(lVar13 + 0x18) = uVar7;                                   // w0f
*(uint *)(*(longlong *)(lVar13 + 0x18) + 4) = uVar28;                // w1f
*(uint *)(*(longlong *)(lVar13 + 0x18) + 8) = uVar4 >> 0x10 ^ uVar4; // w2f
*(uint *)(*(longlong *)(lVar13 + 0x18) + 0xc) = uVar3 >> 0x10 ^ uVar3; // w3f
```

**Pass B vs Pass A swfinalize differences:**

| Line | Pass A | Pass B |
|---|---|---|
| w0 input var | `uVar7` | `uVar7` (same name) |
| w1 input | `uStack_2b8` | `uStack_2c8` (**different var!**) |
| w2 input | `uStack_2c8` | `uStack_2b8` (**swapped with w1!**) |
| w3 input | `uVar6` | `uVar6` (same variable, different value) |
| temp vars | `uVar4, uVar7, uVar28` | `uVar3, uVar4, uVar28` (slightly different) |

**The w1/w2 swap is structural:** In Pass A, w1 = `uStack_2b8` and w2 = `uStack_2c8`. In Pass B, w1 = `uStack_2c8` and w2 = `uStack_2b8`. This reflects the swapped assignments during the Pass B keystream loop (lines 1163 vs 1173).

---

## Section 9: Pass B emit loop + transform2 (lines 1273-1505)

### Pass B emit loop (lines 1273-1451)

```c
// LINE 1273: loop condition = len(KS2) (lVar11 = lStack_240 = KS2 string)
if (0 < *(int *)(lVar11 + 8)) {
    do {
        // LINE 1277: read KS2 byte
        auStack_280[0] = FUN_140406270(lVar11);     // KS2[i]

        // LINES 1279-1313: read w0..w3 from SW state
        uVar6 = *(uint *)(lVar13 + 0x10);           // element count
        puVar1 = *(uint **)(lVar13 + 0x18);         // state array pointer

        uVar7 = uVar3;                               // default 0
        if (uVar6 != 0) { uVar7 = *puVar1; }        // w0

        uVar28 = uVar3;                              // default 0
        if (1 < uVar6) { uVar28 = puVar1[1]; }      // w1

        uVar8 = uVar3;                               // default 0
        if (2 < uVar6) { uVar8 = puVar1[2]; }       // w2

        uVar30 = uVar3;                              // default 0
        if (3 < uVar6) { uVar30 = puVar1[3]; }      // w3

        // LINES 1315-1321: TEA update — w0' = fmix(rotl(w1,5) + w0 + delta + i)
        uVar7 = (uVar28 >> 0x1b | uVar28 << 5) + uVar7 + 0x9e3779b9 + uVar4;
        uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uStack_2c8 = uVar7 >> 0x10 ^ uVar7;          // ◄ w0_temp

        // LINES 1323-1331: TEA update — w1' = fmix(rotl(w2,7) ^ w1 ^ w0_temp)
        uVar28 = (uVar8 >> 0x19 | uVar8 << 7) ^ uVar28 ^ uStack_2c8;
        uVar28 = (uVar28 >> 0x10 ^ uVar28) * 0x45d9f3b;
        uVar28 = (uVar28 >> 0x10 ^ uVar28) * 0x45d9f3b;
        uVar28 = uVar28 >> 0x10 ^ uVar28;
        uStackX_18 = (uint *)CONCAT44(uStackX_18._4_4_, uVar28);  // w1' packed

        // LINES 1333-1339: TEA update — w2' = fmix(rotl(w3,11) + w2 + w1')
        uVar28 = (uVar30 >> 0x15 | uVar30 << 0xb) + uVar8 + uVar28;
        uVar28 = (uVar28 >> 0x10 ^ uVar28) * 0x45d9f3b;
        uVar28 = (uVar28 >> 0x10 ^ uVar28) * 0x45d9f3b;
        uVar8 = uVar28 >> 0x10 ^ uVar28;             // ◄ w2'

        // LINES 1341-1347: TEA update — w3' = fmix(rotl(w0_temp,13) ^ w3 ^ w2' ^ i)
        uVar7 = (uVar7 >> 0x13 | uStack_2c8 << 0xd) ^ uVar30 ^ uVar8 ^ uVar4;
        uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uVar7 = (uVar7 >> 0x10 ^ uVar7) * 0x45d9f3b;
        uVar7 = uVar7 >> 0x10 ^ uVar7;                // ◄ hash_acc = w3'

        auStack_298[0] = uVar7;                        // save hash_acc

        // LINES 1351-1405: write back state (same pattern as Pass A)
        **(uint **)(lVar13 + 0x18) = uStack_2c8;      // w0' = uStack_2c8
        *(uint *)(*(longlong *)(lVar13 + 0x18) + 4) = (uint)uStackX_18;  // w1'
        *(uint *)(*(longlong *)(lVar13 + 0x18) + 8) = uVar8;              // w2'
        *(uint *)(*(longlong *)(lVar13 + 0x18) + 0xc) = uVar7;            // w3'

        // LINES 1407-1429: output byte computation
        uStack_2c0 = (uint)uStackX_18 >> 0x1d | (uint)uStackX_18 * 8;    // rotl(w1',3)
        uStack_2b8 = uVar28 >> 0x17 | uVar8 << 9;                        // rotl(w2',9)
        uVar6 = auStack_298[0] << 0x11;                                   // hash_acc << 17

        uVar28 = (int)uVar4 >> 2 & 3;                  // (c >> 2) & 3
        if (uVar28 < *(uint *)(lVar13 + 0x10)) {
            uStackX_18 = (uint *)CONCAT44(uStackX_18._4_4_,
                                          *(undefined4 *)(*(longlong *)(lVar13 + 0x18) +
                                                          (ulonglong)uVar28 * 4));
        } else {
            uStackX_18 = (uint *)((ulonglong)uStackX_18._4_4_ << 0x20);
        }

        // LINES 1431-1443: write output byte
        FUN_1404073c0(lStack_1c8, *(int *)(lStack_1c8 + 0x1c) + 1);
        *(int *)(lStack_1c8 + 0x1c) = *(int *)(lStack_1c8 + 0x1c) + 1;
        pcVar17 = (char *)FUN_1400281e0(*(undefined8 *)(lStack_1c8 + 0x10));

        sVar22 = (sbyte)((uVar4 & 3) << 3);

        *pcVar17 = ((byte)(((uVar7 >> 0xf | uVar6) ^      // rotl(hash_acc,17) ^
                            uStack_2b8 ^                    // rotl(w2',9) ^
                            uStack_2c0 ^                    // rotl(w1',3) ^
                            uStack_2c8) >> sVar22) ^        // w0' >> shift
                    (byte)auStack_280[0]) +                // XOR KS2[i]
                   (char)((uint)uStackX_18 >> sVar22) +    // + state_byte >> shift
                   (char)uStack_2b0 +                       // + H1_xor
                   (char)uVar4;                             // + c

        uVar4 = uVar4 + 1;                                 // c++
        lVar24 = lStack_278;

    } while ((int)uVar4 < *(int *)(lVar11 + 8));           // loop: c < len(KS2)
}
```

**Pass B emit loop vs Pass A differences:**

| Aspect | Pass A | Pass B |
|---|---|---|
| Loop over | DATA bytes (`len(DATA)`) | KS2 bytes (`len(KS2)`) |
| Counter var | `uStack_2c0` | `uVar4` |
| TEA delta | `-0x61c88647` (0x9e3779b9) | `0x9e3779b9` (direct, no negation) |
| w0,TEA sum | `rotl(w1,5) + w0 + delta + i` | `rotl(w1,5) + w0 + delta + i` (same) |
| w1,TEA    | `rotl(w2,7) ^ w1 ^ w0_temp` | `rotl(w2,7) ^ w1 ^ w0_temp` (same) |
| w2,TEA    | `rotl(w3,11) + w2 + w1'` | `rotl(w3,11) + w2 + w1'` (same) |
| w3,TEA    | `rotl(w0_temp,13) ^ w3 ^ w2' ^ i` | `rotl(w0_temp,13) ^ w3 ^ w2' ^ i` (same) |
| Output byte | `rotl(hash,17)^rotl(w3,9)^rotl(w1,3)^w0` | `rotl(hash,17)^rotl(w2',9)^rotl(w1',3)^w0'` |
| Extra terms | `+ H1 + c` | `+ H1_xor (uStack_2b0) + c (uVar4)` |
| State grow ptr | `lVar11` (DATA string) | `lVar13` (SW state) |

### Pass B transform2 (lines 1483-1505)

```c
// LINE 1483: loop condition = len(round3)
if (0 < *(int *)(lStack_1c8 + 8)) {
    do {
        // LINE 1487: read round3 byte
        uVar28 = FUN_140406270(lStack_1c8);               // round3[i]

        // LINE 1489: transform formula (identical structure to Pass A)
        uVar28 = uVar28 ^ (uVar4 >> (sbyte)((uVar6 & 3) << 3)) + uVar7 + uVar6 ^ uVar7;

        // LINE 1491: prev = uVar28 & 0xff
        uVar7 = uVar28 & 0xff;                            // ◄ prev for next iteration

        // LINES 1493-1499: append byte to round4 output
        FUN_1404073c0(lStack_1c0, *(int *)(lStack_1c0 + 0x1c) + 1);
        *(int *)(lStack_1c0 + 0x1c) = *(int *)(lStack_1c0 + 0x1c) + 1;
        puVar16 = (undefined1 *)FUN_1400281e0(*(undefined8 *)(lStack_1c0 + 0x10));
        *puVar16 = (char)uVar28;

        uVar6 = uVar6 + 1;                                // i++
        lVar24 = lStack_278;

    } while ((int)uVar6 < *(int *)(lStack_1c8 + 8));
}
```

**Pass B transform2 vs Pass A differences:**

| Aspect | Pass A | Pass B |
|---|---|---|
| Input | `round1` bytes | `round3` bytes |
| Output | `round2` | `round4` |
| `prev` variable | `uVar4` (self-modifying) | `uVar7` (separate variable) |
| H1 shift source | `uVar6` (= `uStackX_20`) | `uVar4` (= `uStack_2b0 = H1_xor`) |
| Counter | `uVar28` → `plVar15` | `uVar6` (direct) |

---

## Section 10: H3 + Output assembly (lines 1509-1561)

### H3 assembly from round4 bytes (lines 1509-1521)

```c
// LINES 1509-1521: H3 assembled from FIRST 4 bytes of round4 (little-endian)
*(undefined4 *)(lStack_1c0 + 0x1c) = 0;  // reset round4 string cursor

if (3 < *(int *)(lStack_1c0 + 8)) {      // if len(round4) >= 4
    iVar5 = FUN_140406270(lStack_1c0);    // byte 0 (least significant)
    iVar23 = FUN_140406270(lStack_1c0);   // byte 1
    iVar9 = FUN_140406270(lStack_1c0);    // byte 2
    uVar3 = FUN_140406270(lStack_1c0);    // byte 3

    // LINE 1521: little-endian dword assembly
    uVar3 = uVar3 | iVar9 << 8 | iVar23 << 0x10 | iVar5 << 0x18;
    // H3 = (byte3 << 0) | (byte2 << 8) | (byte1 << 16) | (byte0 << 24)
}
```

**H3 formula:**
```
H3 = round4[3] | (round4[2] << 8) | (round4[1] << 16) | (round4[0] << 24)
```
Note: This is **little-endian** dword assembly — bytes are read sequentially and packed in reverse order of reading.

### Output blob construction (lines 1525-1561)

```c
// LINES 1525-1529: open empty output string lStack_1b8
auStack_228[0] = 0;
uStack_224 = 0;
FUN_140407920(&lStack_1b8, uVar14, auStack_228);

// ... (string init boilerplate)

// LINE 1545: append "M2XC" magic (4 bytes)
FUN_140406ce0(lStack_1b8, 0x4d325843);     // 0x4d325843 = "M2XC" in LE = {'M','2','X','C'}

// LINE 1547: append H1 (4 bytes LE)
FUN_140406ce0(lStack_1b8, uStackX_20);

// LINE 1549: append H2 (4 bytes LE)
FUN_140406ce0(lStack_1b8, uStack_2a0 & 0xffffffff);

// LINE 1551: append H3 (4 bytes LE)
FUN_140406ce0(lStack_1b8, uVar3);

// LINES 1553-1561: append round2 bytes after the header
auStack_220[0] = 0;
uStack_21c = *(undefined4 *)(lVar24 + 8);     // len(round2)
auStack_218[0] = 0;
uStack_214 = 0;
FUN_1404069b0(lStack_1b8, &uStack_2a0, auStack_218, auStack_220);
```

**Final M2XC output layout:**
```
Offset  Size  Field
------  ----  -----
 0       4    "M2XC" magic (0x4d325843)
 4       4    H1
 8       4    H2
12       4    H3
16       N    round2 bytes
```

**Total header = 16 bytes.** The notes file says total M2XC = 27 bytes → round2 = 11 bytes = len(KEY).

---

## Quick Reference: All Constant Values

| Constant | Value | Usage |
|---|---|---|
| PRNG scale | `2.3283064365386963e-10 * 2147483647.0` | Scale 36-bit PRNG to double |
| EPOCH offset | `0xfe624e212ac18000U` | FileTime → Unix epoch adjust |
| fmix multiplier | `0x45d9f3b` | fmix hash constant |
| KS1 constant 1 | `0x12345678` | XOR with H1 for KS1 |
| KS1 constant 2 | `0x87654321` | XOR with H2 for KS1 |
| TEA delta | `0x9e3779b9` (or `-0x61c88647`) | TEA key schedule constant |
| w0 init constant | `0x243f6a88` | π fraction (Pass A) |
| w1 init constant | `0x85a308d3` | π fraction (Pass A) |
| w2 init constant | `0x13198a2e` | π fraction (Pass A) |
| w3 init constant | `0x3707344` | π fraction (Pass A) |
| w0f XOR | `0xa5a5a5a5` | swfinalize pattern |
| w1f ADD | `0x3c6ef372` | swfinalize pattern (TEA constant) |
| KS2 magic | `0x19731f72` | KS2 first dword |
| SHA256_K0 (Pass B) | `0x6a09e667` | SHA-256 IV word 0 |
| SHA256_K1 (Pass B) | `0xbb67ae85` | SHA-256 IV word 1 |
| SHA256_K2 (Pass B) | `0x3ec4a656` | SHA-256 IV word 2 (used for w1 init) |
| M2XC magic | `0x4d325843` | Output header magic |

## Quick Reference: Variable Name Mapping

| Semantic | Ghidra name(s) Pass A | Ghidra name(s) Pass B |
|---|---|---|
| H1 | `uStackX_20` | `uStackX_20` (same) |
| H2 | `uStack_2a0` (64-bit) / `uVar6` (32-bit low) | same |
| len(DATA) | `uStack_2a8` / `*(uint *)(lVar24 + 8)` | same |
| first4(KEY) | `*param_3` | `*uStackX_18` |
| w0 (init) | `uVar7` | `uVar7` |
| w1 (init) | `uStack_2b8` | `uStack_2c8` |
| w2 (init) | `uStack_2c8` | `uStack_2b8` |
| w3 (init) | `uVar6` | `uVar6` → packed in `uStackX_18` |
| w0f (final) | `uVar8` | `uVar7` |
| w1f (final) | `uVar28` | `uVar28` |
| c (counter) | `uStack_2c0` | `uVar4` |
| H1_xor | N/A | `uStack_2b0` (H1 ^ 0x6a09e667) |
