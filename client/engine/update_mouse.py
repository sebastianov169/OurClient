"""
updateMouse — réplica literal del binario (FUN_1414a8d20, 147 lineas).

Fuente: Ghidra MCP, re/decomp_mov/updateMouse_core.c.

FISICA EXACTA (verificada 2026-08-14):
    maxSpeed = *(param_1 + 0x388)          (config del server, ~400)
    dir = normalize(mouse_mundo - jugador)
    dist = |mouse_mundo - jugador|         (UNIDADES DEL MUNDO, no px)
    si dist <= maxSpeed: sin fuerza (FUN_1414a94a0 con pos del jugador)
    si no:
        v = clamp(dist, maxSpeed, 3*maxSpeed)
        jugador.x += dir.x * v / (size*2)   (slot 0x1c8 del objeto +0x368)
        jugador.z += dir.z * v / (size*2)   (slot 0x1d0)
        (envio del MOVE: FUN_1414a8a80)
        camara.x += (dir.x*maxSpeed + jugador.x - camara.x) * 0.25 (objeto +0x370)
    fuerza = sqrt(clamp(dist/maxSpeed, 0, 1)) -> *(param_1 + 0x298)

OJO (bug de circulos): la velocidad se aplica a la POSICION LOCAL del
jugador (prediccion del cliente). El server replica la MISMA formula, asi
que la correccion por CLEAR es minima. El visor fallo al usar cdist (px)
en vez de dist (mundo): la prediccion no coincidia con el server -> orbita.
"""

import math


def updateMouse_core(player, mouse_world_x, mouse_world_z, size, max_speed=400.0):
    """Replica FUN_1414a8d20. Devuelve (dir_x, dir_z, fuerza, v_actual).

    player: objeto con .x/.z (posicion actual del jugador, mundo).
    mouse_world: posicion del cursor en coordenadas de MUNDO.
    size: radio de la celula (param_2 del binario; velocidad / (size*2)).
    """
    dx = mouse_world_x - player.x
    dz = mouse_world_z - player.z
    dist = math.hypot(dx, dz)
    if dist <= 0.0:
        return 0.0, 0.0, 0.0, 0.0
    dir_x, dir_z = dx / dist, dz / dist

    if dist <= max_speed:
        # sin fuerza: FUN_1414a94a0 (mantiene la posicion del jugador)
        fuerza = 0.0
    else:
        # v = clamp(dist, maxSpeed, 3*maxSpeed)
        v = max_speed if dist < max_speed else (3.0 * max_speed if dist > 3.0 * max_speed else dist)
        # prediccion local: pos += dir * v / (size*2)  (slots 0x1c8/0x1d0)
        player.x += dir_x * v / (size * 2.0)
        player.z += dir_z * v / (size * 2.0)
        fuerza = math.sqrt(min(1.0, max(0.0, dist / max_speed)))

    return dir_x, dir_z, fuerza, dist
