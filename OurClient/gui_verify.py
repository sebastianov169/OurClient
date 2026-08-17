"""Verificacion FINAL de la GUI: corre OurClient/main.py headless con el
mouse SIMULADO moviendose (como un jugador real) y mide si la celula
virtual se mueve (spawn_pos actualizado por el 0x2e del server).
"""
import os, sys, threading, time, math
os.environ['SDL_VIDEODRIVER'] = 'dummy'
sys.path.insert(0, '.')

import pygame
pygame.init()
pygame.font.init()

from OurClient.world import World
from OurClient.view import View
from OurClient.network import Network, build_args, load_device_id

W, H = 1280, 720
world = World()
view = View(world, W, H)
args = build_args(load_device_id(), os.path.join('.', 'embedded_rsa_private_14.pem'),
                  '', 'europe', 5)
net = Network(world, args)
net.on_spawn = lambda x, z: setattr(world, "spawn_pos", (x, z))
stop = threading.Event()
threading.Thread(target=net.run, args=(stop,), daemon=True).start()


def _send(net, view, angle, power):
    main = view.world.main_cell
    if main is None or main.grid_x is None:
        return
    tx = main.grid_x + math.cos(angle) * 800
    tz = main.grid_y + math.sin(angle) * 800
    net.udp_move(tx, tz, main.grid_x, main.grid_y, power=power)

# esperar spawn (hasta 60s), luego mover el mouse en circulo como un jugador
t0 = time.time()
while time.time() - t0 < 60 and (world.spawn_pos is None or not world.spawned):
    time.sleep(0.5)

print("=== GUI-VERIFY ===", flush=True)
print("spawn=%s spawned=%s" % (world.spawn_pos, world.spawned), flush=True)
if world.spawn_pos is None:
    print("SIN_SPAWN", flush=True)
    stop.set()
    sys.exit(0)

p0 = world.spawn_pos
max_delta = 0.0
t_m = time.time() + 30
ang = 0.0
while time.time() < t_m:
    # mouse en circulo alrededor del centro (el jugador lo mueve asi)
    ang += 0.4
    mx = W / 2 + math.cos(ang) * 300
    my = H / 2 + math.sin(ang) * 300
    view.update_mouse(mx, my, send_move=lambda a, p: _send(net, view, a, p))
    # render 1 frame (como la GUI real)
    view.update_camera(1 / 60)
    if world.spawn_pos is not None:
        d = math.hypot(world.spawn_pos[0] - p0[0], world.spawn_pos[1] - p0[1])
        if d > max_delta:
            max_delta = d
    time.sleep(0.05)

main = world.main_cell
print("pos_final=%s DELTA=%.1f main=%s masa=%.1f" % (
    world.spawn_pos, max_delta,
    main.eid if main is not None else None,
    main.masa if main is not None else 0), flush=True)
print("OK" if max_delta > 100 else "FALLO", flush=True)
stop.set()
