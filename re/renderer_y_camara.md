# Renderer y Cámara — MitosisOG.exe (verificado en binario)

> Verificado con Ghidra + decompilados guardados en `re/_re_cam/` (11 archivos .c) el 2026-08-13.
> Renderer REAL: **Away3D (Stage3D/OpenGL)** vía fkengine (NO lime/Canvas 2D).
> Clase View (FUN_140795df0) = game loop + renderer (decomp completo en `re/_decomp_140795df0_full.txt`).

---

## 0. Resumen ejecutivo

1. **Proyección mundo→pantalla** (función real `FUN_14077c150` setCameraPosition):
   ```
   screenX = (worldX - camX) * scale + W/2
   screenY = (worldZ - camZ) * scale + H/2
   ```
   Cámara centrada en el jugador, SIN rotación ni perspectiva. `camX = camPos+0xc`, `camZ = camPos+0x14` (la y=altura va en +0x10 y NO participa en pantalla).
2. **Scale** = `*(*(view+0x2b0)+0x38)` (objeto cámara/frustrum) — el zoom es fit-to-size con clamp [min,max] y suavizado `/10` por frame.
3. **Radio visual**: `RADIO = floor(sqrt(masa)*10 + 0.5)` (línea 1010: floor(dVar24*10.0+0.5), FUN_141bf6990=sqrt); **diámetro = 2*radio**; `radio_px = radio_world * scale`. Tamaño mínimo de célula: `if (sizePx<=0.0) sizePx=100.0`.
4. **Frustrum/culling**: rectángulo mundo `[camX - (W/scale)/2 - 10, camZ - (H/scale)/2 - 10, W/scale+20, H/scale+20]` recomputado CADA frame (líneas 556-565).
5. **zOrder = size (masa)** — confirmado el patrón Flash viejo (`setZOrder`/`_zOrder` strings en 141dc2ec0/141dc3000/141dc3858); `sortByZOrder` (FUN_140a24c70) re-ordena ascendente cada frame cuando la entidad marca `_hasFrustrum`/`setFrustrumDirty` — los más pequeños DETRÁS.

---

## 1. Proyección mundo → pantalla (verificada)

```c
// FUN_14077c150 (setCameraPosition) — decompilado REAL
worldContainer.x = DAT_1421b8d98 * 0.5 - camX * scale;   // DAT_1421b8d98 = ancho diseño
worldContainer.y = DAT_1421b8d80 * 0.5 - camZ * scale;   // DAT_1421b8d80 = alto diseño
camera3D.x = (screenH_actual * 0.5 - DAT_1421b8d98 * 0.5) + camX * scale;
camera3D.y = (screenH_actual * 0.5 - DAT_1421b8d80 * 0.5) + camZ * scale;
// scale = *(*(view+0x2b0)+0x38)   (objeto cámara/frustrum)
// camX  = *(camPos+0xc)  ;  camZ = *(camPos+0x14)   (y=altura en +0x10, no participa)
```

**En pygame** (W, H = resolución interna del cliente):
```python
screen_x = (world_x - cam_x) * scale + W / 2.0
screen_y = (world_z - cam_z) * scale + H / 2.0
```

**Cámara suavizada**: `pos += (target - pos) * 0.125` por frame (líneas 850-855).

---

## 2. Radio visual (verificada en código)

```c
// update de cámara (FUN_140795df0, líneas 1009-1018)
dVar26 = FUN_140688820(lVar2) * 2.0;              // diámetro = 2 * masa_radial
// conversión masa -> radio:
dVar24 = FUN_141bf6990(masa);                     // sqrt
radio  = floor(dVar24 * 10.0 + 0.5);              // RADIO = floor(sqrt(masa)*10 + 0.5)
// en pantalla: radio_px = radio_world * scale
// zoom: tamaño mínimo de célula
if (sizePx <= 0.0) sizePx = 100.0;                // líneas 861-864
```

---

## 3. Frustrum / culling (verificada)

```c
// líneas 556-565 (recomputado CADA frame)
frustrum = [ camX - (W/scale)/2 - 10,
             camZ - (H/scale)/2 - 10,
             W/scale + 20,
             H/scale + 20 ]
```

Solo se dibujan las entidades dentro de ese rectángulo mundo.

---

## 4. zOrder (verificada)

- Strings: `setZOrder`/`zorder`/`_zOrder` (141dc2ec0/141dc3000/141dc3858), `resetZOrder`, `sortByZOrder`, `needsResetZorder` en las clases de ENTIDADES (xrefs FUN_1406557a0, FUN_14065b570, FUN_14065fd90, FUN_140666100, FUN_14068a820).
- Getter zOrder (FUN_1406529a0) devuelve el campo de **SIZE**; resetZOrder re-lee el tamaño → **zOrder = size (masa/radio)**.
- sortByZOrder (FUN_140a24c70, decomp en `_re_cam`) re-ordena la lista de dibujo cada frame cuando la entidad marca `_hasFrustrum`/`setFrustrumDirty`; **orden ascendente por zOrder (= size), los más pequeños detrás** (los grandes encima, como el juego real).

---

## 5. Para el visor pygame (resumen ejecutable)

```python
# estado
cam_x, cam_z = jugador.x, jugador.z          # cámara centrada en el jugador
scale = calcular_zoom(...)                    # fit-to-size con clamp [min,max], suavizado /10

# proyección de cada entidad
sx = (ent.x - cam_x) * scale + W / 2.0
sy = (ent.z - cam_z) * scale + H / 2.0

# radio
r_world = floor(sqrt(masa) * 10.0 + 0.5)
r_px = max(r_world * scale, 1.0)

# culling (frustrum mundo)
if not (cam_x - (W/scale)/2 - 10 <= ent.x <= cam_x + (W/scale)/2 + 10 and
        cam_z - (H/scale)/2 - 10 <= ent.z <= cam_z + (H/scale)/2 + 10):
    continue  # fuera de vista

# z-order: dibujar en orden ascendente de masa (pequeños detrás)
entities.sort(key=lambda e: e.masa)

# cámara suavizada
cam += (target_cam - cam) * 0.125
```
