# OurClient — Cliente Python de MitosisOG

Cliente de juego **MitosisOG** (agar.io-like) reimplementado en Python,
replicando la arquitectura del binario original (Haxe/OpenFL):

- **Engine** — game loop fixed-timestep 16.66ms (`OurClient/engine.py`)
- **Network** — login HTTP + TCP desturple/m2xc + hooks AMF3
  (`OurClient/network.py` + `mito_client/`)
- **World** — entidades del mundo con la fábrica del binario
  (`OurClient/world.py` + `client/`)
- **View** — cámara STUCK, input del mouse, render del mundo
  (`OurClient/view.py`)
- **HUD** — lobby, leaderboard, minimapa, stats (FPS/PING/SRV)
  (`OurClient/hud.py`)

## Requisitos

- Python 3.11+
- pygame 2.6+

```bash
pip install pygame
```

## Uso

```bash
python OurClient/main.py --mode 5 --server europe
```

| Modo | Valor |
|------|-------|
| SALAS | 0 (joinroom por nombre) |
| CTF   | 3 |
| FFA   | 5 |
| HVZ   | 7 |

## Controles

| Tecla | Acción |
|-------|--------|
| Mouse | Dirigir la célula (el movimiento sale ~10 Hz por TCP 10022 + refuerzo UDP) |
| SPACE | SPLIT (frame claro TCP `[len][len][0x40][10010]`) |
| W     | EJECT (frame claro TCP `[len][len][0x40][10011]`) |
| ENTER | Jugar / Reaparecer |
| Q     | Salir |

## Flujo de sesión

1. Login HTTP (knock/LIM/EH) + joinroom
2. Connect raw al server del modo → GREETING → AUTH m2xc → PROOF → READY
3. SPAWNED `[20]` → identificación de la propia por `owner == account_id`
   del CLEAR (0x04) o marca `0x1c`
4. MOVE continuo TCP claro `10022` + refuerzo UDP 3724
5. Muerte `[25]` → lobby → AUTO-RESPAWN (toggle en el lobby, ON por defecto)

## Notas de protocolo

- El **MOVE real** es un frame TCP **claro** (sin cifrar):
  `[len:u32][len:u32][0x40][opcode:u32=10022][time:f32][angle:f32][power:f32]`
- El **SPLIT** es `[len][len][0x40][10010]` sin argumentos
- El reenvío periódico de `CLIENT_ENTITIES_INFO` (10002, cada 30s) es
  necesario: sin él el server corta la sesión a los ~20s
- Los PONGs responden 1:1 a los PINGs del server (`[10001, ts, seed%100]`)

## Estructura

```
OurClient/       cliente nuevo (main, network, world, view, hud, engine)
client/          clases del binario traducidas (entities, world, engine, ui)
mito_client/     red verificada (login, keepalive, tcp client, m2xc)
re/              parsers del wire (haxe_clear_parser, amf3_full) + docs
tools/           utilidades de diagnóstico y captura de ventana
tcp_full.py      protocolo TCP (frames, desturple, m2xc, AMF3)
mito_view.py     visor legacy (referencia del render)
```

> Proyecto de ingeniería inversa con fines educativos. No incluye el
> binario del juego, claves privadas ni credenciales.
