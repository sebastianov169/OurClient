#!/usr/bin/env python3
"""
headless_bot.py - Headless MitosisOG bot (petition-based, sin abrir el cliente)

Flujo completo:
  1. HTTP login (do=knock → lim → eh)  [reutiliza tcp_full.do_login]
  2. do=connect → obtiene server:port + token
  3. TCP raw 443: greeting → AUTH(AMF3+AES-CBC) → READY → NATIVE_PLAY
  4. Main loop: auto-PONG, keepalive MOVE, UDP init + UDP move (3724)
  5. Action script: secuencia de acciones de juego sintetizadas
     idénticas al binario (frames AMF3/resturple + CLEAR + UDP)

Uso:
  python headless_bot.py --region europe --mode 3 --duration 300
  python headless_bot.py --actions "wait:5;chat:hola;move:100,50,0.93;jump;emote:1"
  python headless_bot.py --actions-file actions.json --reconnect 3

Requiere: tcp_full.py (raíz del repo), full_login_and_api.py, qw.sol, clave attestation.
"""
import os, sys, json, time, random, argparse, threading

# ── Cargar toolkit desde la raíz del repo ────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
import tcp_full as T   # login HTTP + TCP frames + UDP + GameClient

from tcp_full import (
    do_login, do_connect, make_http_play_fn, spawn_account,
    TL, GameState, GameClient, MODES, REGIONS,
)

# =====================================================================
# ACTION SCRIPT — sintaxis: acc:arg1,arg2;acc2:...;wait:2
# =====================================================================
ACTION_HELP = {
    "wait":      "wait:seconds",
    "chat":      "chat:mensaje",
    "emote":     "emote:id",
    "move":      "move:x,y,power",
    "jump":      "jump",
    "dash":      "dash:angle,power",
    "ability":   "ability:id,x,y",
    "item":      "item:slot",
    "drop":      "drop:slot",
    "equip":     "equip:slot",
    "unequip":   "unequip:slot",
    "attack":    "attack:target,weapon,angle,power",
    "interact":  "interact:target,type",
    "buy":       "buy:item_id,qty",
    "team":      "team:id",
    "respawn":   "respawn",
    "udp":       "udp:x,angle,power",
    "report":    "report:target,razon",
}

def parse_actions(spec):
    """'chat:hola;move:100,50;wait:2' -> [('chat',['hola']), ('move',['100','50']), ('wait',['2'])]"""
    actions = []
    for part in spec.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            name, args = part.split(":", 1)
            args = [a.strip() for a in args.split(",")] if args else []
        else:
            name, args = part, []
        actions.append((name.strip(), args))
    return actions

def run_action_script(client, state, actions):
    """Ejecuta la secuencia de acciones sobre el GameClient (thread del main loop)."""
    for name, args in actions:
        try:
            if name == "wait":
                time.sleep(float(args[0]))
                continue
            elif name == "chat":
                client.send_chat(args[0] if args else "hola")
            elif name == "emote":
                client.send_emote(int(args[0]))
            elif name == "move":
                x, y = float(args[0]), float(args[1])
                power = float(args[2]) if len(args) > 2 else 0.9309
                client.move_to(x, y, power)
            elif name == "jump":
                client.jump()
            elif name == "dash":
                client.dash(float(args[0]), float(args[1]) if len(args) > 1 else 1.0)
            elif name == "ability":
                client.use_ability(int(args[0]), float(args[1]) if len(args) > 1 else 0,
                                   float(args[2]) if len(args) > 2 else 0)
            elif name == "item":
                client.use_item(int(args[0]))
            elif name == "drop":
                client.drop_item(int(args[0]))
            elif name == "equip":
                client.equip(int(args[0]))
            elif name == "unequip":
                client.unequip(int(args[0]))
            elif name == "attack":
                target = int(args[0])
                weapon = int(args[1]) if len(args) > 1 else 0
                angle = float(args[2]) if len(args) > 2 else 0
                power = float(args[3]) if len(args) > 3 else 1.0
                client.attack(target, weapon, angle, power)
            elif name == "interact":
                client.interact(int(args[0]), int(args[1]) if len(args) > 1 else 0)
            elif name == "buy":
                client.buy_item(int(args[0]), int(args[1]) if len(args) > 1 else 1)
            elif name == "team":
                client.set_team(int(args[0]))
            elif name == "respawn":
                client.respawn()
            elif name == "udp":
                x = float(args[0])
                angle = float(args[1]) if len(args) > 1 else -3.084
                power = float(args[2]) if len(args) > 2 else 0.9309
                client.send_udp_move(x, angle, power)
            elif name == "report":
                client.report(int(args[0]), args[1] if len(args) > 1 else "")
            else:
                TL.log("  [bot] ACCION DESCONOCIDA: %s" % name)
        except Exception as e:
            TL.log("  [bot] ERROR en %s(%s): %s" % (name, args, e))
        time.sleep(0.2)
    TL.log("  [bot] Script de acciones completo (%d acciones)" % len(actions))

# =====================================================================
# BOT HEADLESS
# =====================================================================
def run_headless(region="europe", mode_index=1, mode_val=3,
                 duration=300, spawn_wait=120, actions=None,
                 no_http_play=False, quiet=True):
    """Login → connect → spawn → ejecutar acciones → mantener vivo."""
    if not quiet:
        print("\n[bot] === LOGIN HTTP ===")
    sk, magic, session = do_login()
    if not quiet:
        print("[bot] Login OK, sk=%s..." % sk[:16])

    # Stats para nombre de cuenta
    try:
        stats = T.make_api_call(session, sk, magic, {"do": "stats"})
        account = "?"
        for item in stats.get("data", []):
            if item[0] == "previous_user":
                account = item[1]
                break
    except Exception:
        account = "?"
    TL.log("[bot] Cuenta: %s" % account)

    # Conectar y obtener servidor
    if not quiet:
        print("[bot] do=connect (%s, mode=%d)..." % (region, mode_val))
    result = do_connect(session, sk, magic, region, mode_index, mode_val)
    server = result.get("data", {}).get("server", "")
    token = result.get("data", {}).get("token", "")
    if not server or not token:
        TL.log("[bot] ERROR: sin server/token: %s" % json.dumps(result)[:200])
        return False
    parts = server.split(":")
    host = parts[0]
    port = int(parts[1]) if len(parts) > 1 else 443
    TL.log("[bot] Servidor TCP: %s:%d" % (host, port))

    # Play HTTP en paralelo (necesario para spawn)
    http_play = None if no_http_play else make_http_play_fn(session, sk, magic, mode_index, mode_val)

    # Session TCP+UDP completa (reutiliza run_tcp_session de tcp_full)
    spawned = T.run_tcp_session(
        host, port, token, mode=mode_val, duration=duration,
        http_play_fn=http_play, spawn_wait=spawn_wait,
        native_repeats=2, test_mode=True,
        action_fn=(lambda client, state: run_action_script(client, state, actions)) if actions else None,
    )
    return spawned

# =====================================================================
# CLI
# =====================================================================
def main():
    ap = argparse.ArgumentParser(
        description="MitosisOG headless bot (petition-based, sin cliente)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Acciones:\n  " + "\n  ".join("%-9s %s" % (k, v) for k, v in ACTION_HELP.items()))
    ap.add_argument("--region", default="europe", choices=REGIONS)
    ap.add_argument("--mode", type=int, default=3, help="mode_val (3=FFA)")
    ap.add_argument("--mode-index", type=int, default=1)
    ap.add_argument("--duration", type=int, default=300, help="segundos de sesión")
    ap.add_argument("--spawn-wait", type=int, default=120, help="timeout de spawn")
    ap.add_argument("--actions", default=None,
                    help="script: 'wait:5;chat:hola;move:100,50,0.93;jump;emote:1'")
    ap.add_argument("--actions-file", default=None, help="JSON/archivo de acciones")
    ap.add_argument("--no-http-play", action="store_true")
    ap.add_argument("--reconnect", type=int, default=1, help="reintentos de sesión")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    # Cargar acciones
    actions = None
    if args.actions_file:
        with open(args.actions_file, encoding="utf-8") as f:
            spec = f.read().strip()
        actions = parse_actions(spec)
        print("[bot] Acciones desde %s: %d" % (args.actions_file, len(actions)))
    elif args.actions:
        actions = parse_actions(args.actions)
        print("[bot] Acciones: %s" % "; ".join("%s(%s)" % (n, ",".join(a)) for n, a in actions))

    # Ejecutar con reintentos
    attempt = 0
    while attempt < args.reconnect:
        attempt += 1
        print("\n[bot] === Intento %d/%d ===" % (attempt, args.reconnect))
        try:
            spawned = run_headless(
                region=args.region, mode_index=args.mode_index, mode_val=args.mode,
                duration=args.duration, spawn_wait=args.spawn_wait,
                actions=actions, no_http_play=args.no_http_play,
                quiet=not args.verbose)
        except Exception as e:
            TL.log("[bot] ERROR sesión: %s" % e)
            spawned = False

        if spawned:
            print("[bot] RESULTADO: SPAWNED OK")
            break
        else:
            print("[bot] RESULTADO: FAILED (intento %d)" % attempt)
            if attempt < args.reconnect:
                time.sleep(5)

    sys.exit(0 if spawned else 1)

if __name__ == "__main__":
    main()
