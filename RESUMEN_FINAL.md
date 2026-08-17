# M2XC Login — Documentación Completa

---

## Estado Actual (20 Jul 2026 — ACTUALIZADO ✅)

| Componente | Estado | Detalle |
|-----------|--------|---------|
| KNOCK | ✅ | Funciona con `?do=knock` |
| LIM | ✅ | Funciona con `ddd=0` + `did=AES_encrypted` |
| **DTF** | ✅ **Puro Python** | `m2xc_encrypt()` legacy con user_id="957545304" |
| **DD** | ✅ **Puro Python** | `m2xc_encrypt_full()` exact con proof_json+magic |
| Proof | ✅ | RSA-2048 PKCS1v15 SHA256 con embedded key |
| MS | ✅ | RSA encrypt con session key |
| **EH** | ✅ **JSON RESPONSE** | `{"result":"ok","message":"wh","time":0,"data":{...}}` |
| **Byte-match vs Game** | ⚠️ **6/834 (0.7%)** | Swfinalize corregido pero aún difiere |

## CORRECCIONES (20 Jul 2026)

### Bug #1: swfinalize Pass A — w2f usaba f2i en vez de w0 original
**Archivos:** `m2xc_exact.py`, `m2xc_encrypt.py`

La fórmula C (línea 741) usa `(w0f >> 19 | w0_original << 13) ^ w2_original`,
donde `w0_original` es el valor del keystream ANTES de aplicar fmix2.
Nuestro código usaba `f2i` (segundo resultado de f2) en vez de `w0_original`.

### Bug #2: swfinalize Pass B — fórmulas DIFERENTES de Pass A
**Archivos:** `m2xc_exact.py`, `m2xc_encrypt.py`

Pass B usa:
- w2f = fmix((w0f >> 19 | **f2_first_w1** << 13) ^ w2_orig) — usa f2_first de w1
- w3f = fmix((w1f << 9 | **f2_first_w1** >> 23) + **w2f**) — usa f2_first_w1, NO w3

Pass A usa:
- w2f = fmix((w0f >> 19 | **w0_orig** << 13) ^ w2_orig) — usa w0 ORIGINAL
- w3f = fmix((w1f << 9 | **f2i_w1** >> 23) + w2f) — usa f2i (SEGUNDO f2)

Antes del fix, AMBOS passes usaban la misma fórmula INCORRECTA.

## ARCHIVOS

| Archivo | Descripción |
|---------|-------------|
| `login_final_v9.py` | **LOGIN con swfinalize corregido** |
| `login_final_v8.py` | **LOGIN 100% Python puro** (legacy, funcional) |
| `m2xc_exact.py` | **Implementación byte-exacta** (CORREGIDA) |
| `m2xc_encrypt.py` | Implementación legacy (CORREGIDA) |
| `__m2xc_full_test.py` | Suite de tests vs Ghidra decomp |
| `frida_trace_m2xc.py` | **Frida: captura estado M2XC del juego** |
| `compare_states.py` | **Comparación Python vs Game** |
| `frida_state_dump.json` | (pendiente: ejecutar frida_trace_m2xc.py) |
| `dtf_listo.py` | Biblioteca DTF con mix+cifrado |
| `RESUMEN_FINAL.md` | Este archivo |

## ESTRUCTURA DE FUN_1403df080 (Ghidra)

```
FUN_1403df080(param_1=output, param_2=DATA, param_3=KEY)

Fase 0: Setup
  - H1 = FUN_1404054c0(time_seed, rand)       → uStackX_20
  - H2 = seed2 ^ fmix(len(KEY) ^ H1 ^ len(DATA)) → uStack_2a0

Fase 1 (Pass A):
  a) State Init: 4x fmix con constantes SHA-like
  b) Keystream XXTEA: itera KEY bytes, actualiza state
  c) Finalize: w2f usa w0 ORIGINAL, NO f2i
     w2f = fmix((w0f >> 19 | w0 << 13) ^ w2)
     w3f = fmix((w1f << 9 | f2i_w1 >> 23) + w2f)
  d) Emit Loop (TEA table): procesa DATA bytes → round1
  e) Transform2: XOR mixing → round2 (= payload)

Fase 2 (Pass B):
  a) KS2 = [0x19731f72, H1, H2, len(DATA), len(round2)] + round2
  b) State Init (constantes SHA-256, DIFFERENTES de Pass A)
  c) Keystream XXTEA: itera KEY bytes
  d) Finalize (FÓRMULAS DIFERENTES de Pass A):
     w2f = fmix((w0f >> 19 | f2_first_w1 << 13) ^ w2)
     w3f = fmix((w1f << 9 | f2_first_w1 >> 23) + w2f)
  e) Emit Loop (Pass B variant): procesa KS2 → round3
  f) Transform2 → round4
  g) H3 = first 4 bytes of round4 (LE uint32)

Output: M2XC(4) + H1(4) + H2(4) + H3(4) + round2( payload )
```

## EMIT LOOP — DIFERENCIAS Pass A vs Pass B

| Componente | Pass A | Pass B |
|-----------|--------|--------|
| Seed term | H1 | H1 ^ 0x6a09e667 (seed_a) |
| xor term2 | hash_acc (acumulado) | ROL(w2, 9) (fresco) |
| Finalize w2f usa | w0_original | f2_first_w1 |
| Finalize w3f usa | f2i_w1 + w2f | f2_first_w1 + w2f |
| Data origen | DATA bytes | KS2 bytes |
| Transform2 ha/hb | H1 / H2 | seed_a / seed_b |

## RESULTADOS DE VERIFICACIÓN vs CAPTURA #3 (DD)

| Componente | Antes del fix | Después del fix |
|-----------|---------------|-----------------|
| Payload match | 2/834 (0.2%) | 6/834 (0.7%) |
| w2f Pass A | 0x70FE4C07 (incorrecto) | 0x9BC393D8 (Ghidra-correcto) |
| Tests pasan | N/A | 7/7 ✅ |

## PROBLEMAS CONOCIDOS (byte-level)

1. **Solo 6/834 bytes coinciden** — hay más diferencias sutiles en:
   - Keystream (posible offset de contador TLS)
   - Transform1/emit loop (posibles diferencias en selección de tabla)
   - Transform2 (posible diferencia en contador inicial)
2. **Para encontrar el resto**: ejecutar `frida_trace_m2xc.py` para capturar
   estado interno real del juego (w0,w1,w2,w3 en cada paso del emit loop)

## PRÓXIMOS PASOS

1. **Capturar estado interno**: `python frida_trace_m2xc.py` mientras el juego
   hace login. Captura KEK (keystream), estado finalizado, y TEA state.
2. **Comparar**: `python compare_states.py` con el dump capturado.
3. **Corregir**: Ajustar fórmulas según diferencias encontradas.
4. **Repetir** hasta coincidencia byte-exacta.

## CONCLUSIÓN

✅ **login_final_v9.py funcional** — 100% Python puro, SIN Frida  
✅ **EH devuelve JSON exitoso** con M2XC corregido  
✅ **Bug de swfinalize identificado y corregido** (Pass A + Pass B)  
✅ **Frida trace infraestructura lista** para debugging fino  
⚠️ **Match byte-level: 6/834** — requiere más investigación

La clave del éxito para login:
1. El servidor NO valida byte-exacto el M2XC
2. `build_dtf_from_python()` produce DTF válido
3. NO usar `de=desktop` (causa body vacío en replay)
4. `m2xc_encrypt_full()` con two-pass y swfinalize corregido es aceptado
