# Opcodes del protocolo MitosisOG (extraidos de Ghidra)

Fuente: tabla de strings del binario MitosisOG.exe (0x141dc81e8+),
clase `fkengine.game.data.Opcodes`. Nombres reales del protocolo.

## Server -> Client (OP_*)

| Opcode | Nombre real | Notas |
|--------|-------------|-------|
| 1 | OP_PING | El server hace ping, el cliente responde PONG |
| 4 | OP_PLAYERID | Asigna el player_id al cliente |
| 52 | OP_SECURE_NONCE / AUTH_TOKEN | Token de autenticacion post-AUTH |
| 40 | OP_CONFIRM_UDP / SERVER_ACK | Ack del server |
| 20 | OP_ENTITIES_INFO (spawn) | Posicion de spawn del jugador |
| - | OP_BEGIN | Inicio de partida |
| - | OP_LOAD | Carga de mapa |
| - | OP_LAG | Lag del cliente |
| - | OP_ENTITY_EVENT | Evento de entidad |
| - | OP_EVENT | Evento generico |
| - | OP_ENTITIES_INFO | Info de entidades (lista) |
| - | OP_MAP | Datos del mapa |
| - | OP_FRAME | Frame de juego (CLEAR, 0x64) |
| - | OP_ENTITIES_STATUS | Estado de entidades |
| - | OP_PLAYER_STATUS | Estado del jugador |
| - | OP_ERROR | Error |
| - | OP_TEAM_GAME_ENDED | Fin de partida por equipo |
| - | OP_PLAYER_UPDATE | Update del jugador |
| - | OP_ENTITY | Entidad individual |
| - | OP_ROAD | Camino/trayectoria |
| - | OP_EARN_COINS | Ganar monedas |
| - | OP_CAMERA_POSITION | Posicion de camara |
| - | OP_CHART_DATA | Datos de grafico |
| - | OP_INVITE_CODE | Codigo de invitacion |
| - | OP_DURABILITY | Durabilidad de items |
| - | OP_EXPERIENCE_GAIN | Ganancia de XP |
| - | OP_STOP_WIN_WITHIN | Detener cuenta regresiva de victoria |
| - | OP_WIN_WITHIN | Cuenta regresiva de victoria |
| - | OP_WAITING_FOR_PLAYERS | Esperando jugadores |
| - | OP_FLAG_RESET_TIME | Reset de bandera (CTF) |
| - | OP_POWER_READY | Poder listo |
| - | OP_POWER | Poder |
| - | OP_UPDATE_NEWS | Noticias |
| - | OP_MESSAGE | Mensaje |
| - | OP_GAME_ENDED | Fin de juego |
| - | OP_BEGINS_IN | La partida empieza en X |
| - | OP_SHOW_IMAGE | Mostrar imagen |
| - | OP_MATCH_STARTED | Partida iniciada |
| - | OP_CHAT_MESSAGE | Mensaje de chat |
| - | OP_SHOW_MAP | Mostrar mapa |
| - | OP_ENTITY_BALOON | Globo de entidad |
| - | OP_CONNECTION_RESUME_KEY | Clave de reanudacion |
| - | OP_TEST_MERSENNE | Test de Mersenne Twister |
| - | OP_GAME_ENDS_IN | El juego termina en X |
| - | OP_FLAG_RESET_TIME_TYPE | Tipo de reset de bandera |
| - | OP_LEADERBOARD_OVERLAY | Overlay de ranking |
| - | OP_GW_BROADCAST | Broadcast del gateway |
| - | OP_PET_AVAILABLE | Mascota disponible |
| - | OP_DISPLAY_DETAILS | Detalles de display |
| - | OP_CHART_SET_TITLE | Titulo de grafico |
| - | OP_ADDITIONAL_CHART_DATA | Datos adicionales de grafico |
| - | OP_SET_GAME_TIME | Tiempo de juego |
| - | OP_SECURE_NONCE | Nonce seguro (handshake) |
| - | OP_SECURE_CHALLENGE | Challenge seguro |
| - | OP_CONFIRM_UDP | Confirmar UDP |
| - | OP_DESTROY_DETAILS | Destruir detalles |

## Client -> Server (OP_CLIENT_*)

| Nombre real | Notas |
|-------------|-------|
| OP_CLIENT_ENTITIES_INFO | Pedir info de entidades |
| OP_CLIENT_PING_REPLY | Respuesta al ping (PONG) |
| OP_CLIENT_READY | Cliente listo |
| OP_CHANGE_NONCE | Cambiar nonce |
| OP_CLIENT_CLICK | Click |
| OP_CLIENT_MOVE | Movimiento (TCP) |
| OP_CLIENT_ENTITY_COMAND | Comando de entidad |
| OP_CLIENT_BUILD | Construir |
| OP_CLIENT_DOUBLE_TAP | Doble tap |
| OP_CLIENT_FOCUS | Foco |
| OP_CLIENT_CLEAR_ROAD | Limpiar camino |
| OP_CLIENT_ROAD | Camino |
| OP_CLIENT_REFRESH_INVITE | Refrescar invitacion |
| OP_CLIENT_REQUEST_INVITE | Pedir invitacion |
| OP_CLIENT_END_SHOOTING | Dejar de disparar |
| OP_CLIENT_BEGIN_SHOOTING | Empezar a disparar |
| OP_CLIENT_CHAT_MESSAGE | Mensaje de chat |
| OP_CLIENT_TOGGLE_BAN | Banear/desbanear |
| OP_CLIENT_USE_ITEM | Usar item |
| OP_CLIENT_RELEASE_INVITE | Soltar invitacion |
| OP_CLIENT_MOVE_SHORT | Movimiento corto (UDP) |
| OP_CLIENT_TEST_MERSENNE | Test Mersenne |
| OP_CLIENT_PLAYER_UPDATE | Update del jugador |
| OP_CLIENT_REPORT_ABUSE | Reportar abuso |
| OP_CLIENT_END_SPEEDUP | Fin speedup |
| OP_CLIENT_BEGIN_SPEEDUP | Inicio speedup |
| OP_CLIENT_SET_PARENTAL | Control parental |
| OP_CLIENT_CALL_PET | Llamar mascota |
| OP_CLIENT_MOVE_LOOK_AT | Mover y mirar |
| OP_CLIENT_BEGIN_SHOOTING_RADIANS | Disparar en radianes |
| OP_CLIENT_END_CTRL | Fin control |
| OP_CLIENT_BEGIN_CTRL | Inicio control |
| OP_CLIENT_UDP_NOT_AVAILABLE | UDP no disponible |
| OP_CLIENT_CONFIRM_UDP | Confirmar UDP |
| OP_CLIENT_RESIZE_FRUSTRUM | Resize frustrum |
| OP_CLIENT_CONTROL_SETUP | Setup de control |
| OP_CLIENT_EQUIPMENT_DATA | Datos de equipamiento |
| OP_CLIENT_REQUEST_CHANGE_NONCE | Pedir cambio de nonce |
| OP_CLIENT_SECURE_PROOF | Prueba de seguridad (TPM) |

## Frames CLEAR (flag=1, sin desturple)

Los frames CLEAR del server empiezan con 0x64 y son serializacion
binaria custom (no AMF3 estandar). Estructura observada:

- `64 04 0008 0001 [id:4] 0001 0004 002c [val:4]` repetido = lista
  de entidades (OP_ENTITIES_INFO / OP_ENTITIES_STATUS)
- `64 00 01 62 [ts:4] 0001 6d [x:4] 0001 79 [y:4] 0001 a7 [z:4]`
  = frame de posicion/movimiento de entidad (OP_FRAME)
  - 0x62 = timestamp incremental
  - 0x6d = coordenada X
  - 0x79 = coordenada Y
  - 0xa7 = coordenada Z / angulo

## Hash de strings (tabla Haxe)

Cada string OP_* tiene un hash de 4 bytes en la tabla:
- OP_PING = 0xc5656ee7
- Opcodes (clase) = 0x2bbd71cf
- OP_BEGIN = 0x9ab757c5
- OP_PLAYERID = 0x443601b6
