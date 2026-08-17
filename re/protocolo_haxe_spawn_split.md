# Protocolo Haxe de MitosisOG.exe — Spawn (0x14/20), Opcode 30 (0x1e) y SPLIT (0x271a/10010)

**Binario:** `C:\Users\ren\Desktop\og mito\MitosisOG.exe` (cliente Haxe, base 0x140000000)
**Handler analizado:** `FUN_140752e80` (0x140752e80) — handler genérico de paquetes del router `packetReceived@Game` (FUN_140769000 → FUN_140752e80). Decompilado completo en `_decomp_752e80.txt` (1593 líneas).
**Fecha:** 2026-08-13

---

## 0. Resumen ejecutivo

| Mensaje | Opcode | Dirección del case | Qué hace el cliente |
|---|---|---|---|
| Spawn / set de posición | 20 (0x14) | `FUN_140752e80+0x…` (líneas 864–874 de `_decomp_752e80.txt`) | Lee **3 floats** `[x, y, z]` y los copia a un objeto 3D en `Game+0x4a8` (`+0x14=x`, `+0x10=y`, `+0xc=z`). **NO toca masa.** |
| Timer de partida | 30 (0x1e) | líneas 665–680 | Lee **1 int** (ms) → `Game+0x54c` → formatea `M:SS` y lo pinta en pantalla (`FUN_14073ea80` → `FUN_14074d180`). |
| SPLIT (salida) | 10010 (0x271a) | **No está en el handler** — se envía desde `FUN_1407815b0` / `FUN_140781600` | `send(conn, flag=1, 0x271a, args=[])` vía `FUN_14096e330` → `FUN_14096dc40` (websocket) o `FUN_14096fa80` (TCP). **Sin argumentos.** |

**VEREDICTO MASA (y del spawn):** ❌ **REFUTADO.** El 2º valor `[x,y,z]` **NO es masa**. En el case 0x14 no hay ninguna llamada a `FUN_140677760` (setMassAndRadius) ni a `FUN_140685400` (addExp) — de hecho **ninguna llamada a esas funciones existe en todo `FUN_140752e80`** (grep del decompilado completo: 0 coincidencias). El valor se escribe como **float de 4 bytes en offset `+0x10` de un objeto de 3 campos** (x,y,z). Los valores empíricos observados {1, 702, 814, 1184, 1954} son **alturas/posición Y del terreno** (1 = nivel base), no masa.

---

## 1. Mecánica de lectura de campos del handler

- El paquete llega como array Haxe en `local_10b8`.
- El acceso a un elemento usa el vtable del array: `(**(code **)(*local_10b8 + 0xb8))(local_10b8, buffer, índice)` — devuelve/escribe el elemento `índice` en `buffer`.
- La conversión a **float** se hace con `FUN_14007f3e0` (0x14007f3e0):
  ```c
  float FUN_14007f3e0(longlong *param_1) {
    if ((longlong *)*param_1 != (longlong *)0x0) {
      dVar1 = (double)(**(code **)(*(longlong *)*param_1 + 0x40))();  // Number Haxe → double
      return (float)dVar1;                                            // → float 32-bit
    }
    return 0.0;
  }
  ```
- La conversión a **int** usa el mismo vtable `+0x40` (doble→int con truncado), como en el case 0x1e.
- Los opcodes entrantes se leen como int (`FUN_1400219d0`) al inicio del handler; el dispatch es `if (iVar5 == 0xNN)`.

---

## 2. Case 0x14 — opcode 20 (spawn / posición de spawn)

### 2.1 Decompilado citado (`_decomp_752e80.txt`, líneas 864–874)

```c
  if (iVar5 == 0x14) {
    uVar10 = *(undefined8 *)(param_1 + 0x4a8);                                  // objeto destino (Game+0x4a8)
    uVar12 = (**(code **)(*local_10b8 + 0xb8))(local_10b8,local_b78,2);         // lee array[2]
    FUN_14007f3e0(uVar12);                                                       // → float (z)
    uVar12 = (**(code **)(*local_10b8 + 0xb8))(local_10b8,local_b70,1);         // lee array[1]
    FUN_14007f3e0(uVar12);                                                       // → float (y)
    uVar12 = (**(code **)(*local_10b8 + 0xb8))(local_10b8,local_b68,0);         // lee array[0]
    FUN_14007f3e0(uVar12);                                                       // → float (x)
    FUN_141806cb0(uVar10);                                                       // escribe los 3 floats en el objeto
    return;
  }
```

### 2.2 Estructura exacta leída

| Índice del array | Tipo leído | Conversión | Destino final | Campo |
|---|---|---|---|---|
| `[0]` | Number Haxe | `FUN_14007f3e0` → **float 32-bit** | `obj+0x14` | x |
| `[1]` | Number Haxe | `FUN_14007f3e0` → **float 32-bit** | `obj+0x10` | y |
| `[2]` | Number Haxe | `FUN_14007f3e0` → **float 32-bit** | `obj+0x0c` | z |

Se leen **exactamente 3 campos, todos float** (se leen en orden inverso 2,1,0 pero eso es solo el orden de lectura).

### 2.3 El setter `FUN_141806cb0` (0x141806cb0) — decompilado completo

```c
void FUN_141806cb0(longlong param_1, undefined4 param_2, undefined4 param_3, undefined4 param_4)
{
  *(undefined4 *)(param_1 + 0xc)  = param_2;   // array[2] → +0x0c  (z)
  *(undefined4 *)(param_1 + 0x10) = param_3;   // array[1] → +0x10  (y)
  *(undefined4 *)(param_1 + 0x14) = param_4;   // array[0] → +0x14  (x)
  return;
}
```
*(En la llamada `FUN_141806cb0(uVar10)` del case, Ghidra no muestra los 3 floats porque viajan en los registros XMM de la convención x64; la firma de 4 parámetros y la lectura de exactamente 3 elementos lo confirman: los 3 floats leídos se pasan como param_2/3/4.)*

- El objeto destino es `*(Game + 0x4a8)`, un objeto con cabecera de 8 bytes (vtable/tipo) y **3 campos float consecutivos** (+0x0c, +0x10, +0x14) → estructura `{ vtable:0x0, tipo:0x8?, x:0x14, y:0x10, z:0x0c }` (un Vector3/posición Haxe).
- **No hay ningún otro efecto**: no se crea entidad, no se llama a `FUN_140677760`, `FUN_140685400`, `FUN_140678c80` ni a ningún setter de masa en este case.

### 2.4 ¿El 2º valor es MASA? → ❌ NO (REFUTADO)

Evidencia:
1. **Grep de `FUN_140677760` en `_decomp_752e80.txt` completo: 0 coincidencias.** Tampoco aparecen `FUN_140685400` (addExp) ni `FUN_140678c80` (applyParticle).
2. El 2º valor se escribe como `float` en `+0x10` de un objeto de 3 coordenadas, junto a x (+0x14) y z (+0x0c).
3. Para comparación, `setMassAndRadius` = `FUN_140677760` (0x140677760) escribe masa en `Entity+0xC0` (double, `param_1[0x18]`) e `int` en `Entity+0x48` (`*(int *)(param_1 + 0x12)`), y recalcula el radio con `sqrt` (`FUN_141bf6990`) → `radio = floor(sqrt(masa)*10 + 0.5) + 1` vía vtable `+0x1c8`. Sus únicos callers son `FUN_140677830` y `FUN_140789500` (×2) — **ninguno en la ruta del case 0x14**.
4. Conclusión: `[20, [x, y, z]]` son **coordenadas** (float32): y ∈ {1, 702, 814, 1184, 1954} = altura del terreno (1 = nivel base/recién nacido). La masa **no viaja en el spawn**; se asigna por otras vías (comer pellets/food vía addExp, o en el cliente tras el spawn).

---

## 3. Case 0x1e — opcode 30 (timer de partida)

### 3.1 Decompilado citado (`_decomp_752e80.txt`, líneas 665–680)

```c
  if (iVar5 == 0x1e) {
    if (local_10b8 == (longlong *)0x0) {
      dVar24 = 0.0;
    }
    else {
      dVar24 = (double)(**(code **)(*local_10b8 + 0x40))();      // 1er elemento del array → double
      if ((dVar24 < -2147483647.0) || (2147483647.0 < dVar24)) {
        *(int *)(param_1 + 0x54c) = (int)(longlong)dVar24;
        FUN_14073ea80(param_1);
        return;
      }
    }
    *(int *)(param_1 + 0x54c) = (int)dVar24;                     // Game+0x54c = valor (ms)
    FUN_14073ea80(param_1);
    return;
  }
```

### 3.2 Estructura y comportamiento

- Lee **1 solo campo**: el elemento índice 0 del array (vtable `+0x40` = "get first / toDouble"), convertido a **int 32-bit** (con guard de rango).
- Lo escribe en `Game+0x54c` — campo de **tiempo en milisegundos** (se resetea a 0 en el case 10/`iVar6 == 0x1a`, línea 1378–1381: `if (0 < *(int *)(param_1 + 0x54c)) { *(param_1+0x54c) = 0; FUN_140752200(param_1); }`).
- Llama `FUN_14073ea80` (0x14073ea80): `dVar12 = ceil(ms/1000.0)`, calcula `seg = v % 60` y `min = (v - seg)/60`, formatea el string `"M:SS"` (con `FUN_140056b10` / `%d`) y lo **pinta en pantalla** vía `FUN_14074d180(param_1, texto, …)` (el mismo renderizador de texto del case 0x1d).
- Interpretación: **opcode 30 = "updateGameTime"** — el servidor envía el tiempo restante de partida y el cliente actualiza el HUD. No tiene relación con spawn ni masa.

---

## 4. SPLIT — opcode 0x271a (10010)

### 4.1 No está en el handler de entrada
`0x271a` **no aparece en `_decomp_752e80.txt`** (grep: 0 coincidencias). SPLIT es un mensaje **de salida** (cliente → servidor) y se envía desde las funciones de acción del jugador.

### 4.2 Emisores del SPLIT: `FUN_1407815b0` (0x1407815b0) y `FUN_140781600` (0x140781600)

```c
// FUN_1407815b0 (0x1407815b0) — variante 1
void FUN_1407815b0(longlong param_1) {
  lVar1 = *(longlong *)(*(longlong *)(param_1 + 0x310) + 0x10);      // player → cells
  if ((lVar1 != 0) && (*(int *)(lVar1 + 0x10) != 0)) {               // el jugador existe y tiene células
    local_res8[0] = 0;                                               // args = array vacío
    FUN_14096e330(*(undefined8 *)(param_1 + 0x340),                  // conexión (Game+0x340)
                  CONCAT71((int7)((ulonglong)lVar1 >> 8),1),         // flag = 1
                  0x271a,                                            // ★ OPCODE 10010 = SPLIT
                  local_res8);
  }
}

// FUN_140781600 (0x140781600) — variante 2 (closure con retorno)
undefined8 * FUN_140781600(undefined8 *param_1, longlong param_2) {
  lVar1 = *(longlong *)(*(longlong *)(param_2 + 0x310) + 0x10);
  if ((lVar1 != 0) && (*(int *)(lVar1 + 0x10) != 0)) {
    local_res10[0] = 0;
    FUN_14096e330(*(undefined8 *)(param_2 + 0x340), 1, 0x271a, local_res10);
  }
  *param_1 = 0;
  return param_1;
}
```

**Qué hace el cliente:** si el jugador local (`Game+0x310` → lista de células, con count ≠ 0) existe, envía `[10010]` **sin argumentos** (array args vacío) por la conexión `Game+0x340`.

### 4.3 Cadena de envío

```
FUN_1407815b0 / FUN_140781600          (disparo: referencia indirecta — Haxe)
   └─ FUN_14096e330 (0x14096e330)      sender genérico: (conn, flag:byte, opcode:u32, args)
        ├─ si websocket OK (DAT_1421b8a84==1 y conn+0x168): FUN_14096dc40 (0x14096dc40)
        │     └─ FUN_14096df30(conn, &buf, msgId, flag, opcode, args)  → serializa y envía
        │        (msgId = conn+0x198, se incrementa por mensaje; opcode queda en +0x1c del registro)
        └─ si no: FUN_14096fa80 (0x14096fa80)  → envío raw/TCP
```

- `FUN_14096e330` (0x14096e330): `void FUN_14096e330(longlong param_1, undefined1 param_2, undefined4 param_3, longlong *param_4)` — `param_2` = flag de 1 byte, `param_3` = **opcode u32**, `param_4` = array de argumentos. Envía por websocket (`FUN_14096dc40`) o fallback (`FUN_14096fa80`).
- `FUN_14096dc40` (0x14096dc40): asigna msg id `*(int *)(conn+0x198)++`, delega la serialización en `FUN_14096df30(conn, &buf, msgId, flag, CONCAT44(hi, opcode), &args)` y registra un callback con el opcode en `+0x1c`.
- Los xrefs de `FUN_1407815b0`/`FUN_140781600` son solo datos (tablas Haxe en 0x142273fb0 / 0x142273fbc; `FUN_14079d9b0` referencia a `FUN_140781600`) → se invocan indirectamente (closures/eventos Haxe, p. ej. teclado/UI).
- La constante `0x271a` como DWORD inmediato aparece en `.text` del exe SOLO en: `0x140680ca6`, `0x1407815d8` (dentro de FUN_1407815b0), `0x140781630` (dentro de FUN_140781600), `0x140dd5140`, `0x140e52895` → confirma que el único emisor de SPLIT en la clase de acciones es este par.

---

## 5. Tabla de opcodes entrantes identificados en `FUN_140752e80` (referencia)

| Opcode | Línea | Función/efecto |
|---|---|---|
| 0x0b (11) | ~1050 | (no case directo; sub-dispatch 10) |
| 0x0d (13) | 1051 | Recolecta entidades en `Game+0x3a0` |
| 0x0f (15) | 859 | `FUN_14073b220` |
| 0x10 (16) | 947 | Add entity al mundo (`FUN_141766420`, `FUN_1406695a0`) |
| 0x11 (17) | 987 | Añade célula/pellet (usa `FUN_140685f90`, `FUN_1413ec4f0`, `FUN_14072f000`) |
| 0x12 (18) | 1066 | `FUN_14068f830` (lista de entidades) |
| 0x13 (19) | 875 | `(vtable+0x300)` con `Game+0x3d8` |
| **0x14 (20)** | **864** | **SPAWN: 3 floats [x,y,z] → objeto en `Game+0x4a8` (+0x14=x, +0x10=y, +0x0c=z)** |
| 0x15 (21) | 858 | sub-dispatch |
| 0x16 (22) | 738 | Actualización de célula/entidad (`FUN_140690160`, color, tiempo) |
| 0x17 (23) | 782 | Pausa/visibilidad del world (`Game+0x508` vtable+0x238) |
| 0x18 (24) | 627 | `DAT_1421b8c38 += valor` (contador) |
| 0x19 (25) | 794 | (varios) |
| 0x1a (26) | 1378 | Resetea `Game+0x54c` (timer) y llama `FUN_140752200` |
| 0x1c (28) | 737 | (rama) |
| 0x1d (29) | 644 | Texto en pantalla (`FUN_14074d180`) |
| **0x1e (30)** | **665** | **TIMER: 1 int (ms) → `Game+0x54c`, HUD `M:SS` (`FUN_14073ea80`)** |
| 0x1f (31) | 962 | `FUN_14075c380` (objeto 0x18 bytes) |
| 0x21 (33) | 851 | `FUN_1404666a0(DAT_1421b8718, …)` |
| 0x22 (34) | 661 | `FUN_140721d70` (pausa) |
| 0x24 (36) | 623 | `Game+0x5c1 = 1` |
| 0x25 (37) | 1074 | Config/estado del jugador (color, varios campos) |
| 0x26 (38) | 681 | Fin de partida (`Game+0x548`, timeout, `FUN_140741230`) |
| 0x29 (41) | 1261 | (`FUN_1409254d0`, `FUN_140e74600`, …) |
| 0x2b (43) | 1254 | `Game+0x618 = bool` |
| 0x2d (45) | 708 | Fin de partida alternativo (tiempo, color) |
| 0x2f (47) | 926 | `FUN_1414990f0` |
| 0x30 (48) | 932 | `FUN_1403d1ec0` → vtable+0x2f8 |
| 0x31 (49) | 882 | `FUN_141498db0` (3 campos + booleano) |
| 0x32 (50) | 922 | `FUN_141499020` |
| 10 (0x0a) | 1353 | Sub-dispatch por tipo (0x15–0x1e, 0x19, 0x1a) |

## 6. Archivos de evidencia generados (carpeta `re\`)
- `_decomp_752e80.txt` — decompilado completo del handler (ya existía).
- `_decomp_141806cb0.txt/.json` — setter de 3 floats del case 0x14.
- `_decomp_14007f3e0.txt/.json` — lector float.
- `_d_14073ea80.txt` — formateador de timer (case 0x1e).
- `_d_140677760.txt` — setMassAndRadius (referencia, NO se llama en spawn).
- `_d_14096e330.txt`, `_d_14096dc40.txt`, `_d_14096fa80.txt` — cadena de envío.
- `_d_1407815b0.txt`, `_d_140781600.txt` — emisores SPLIT (0x271a).
- `_x_*.txt` — xrefs (sender, emisores, setMass).
