"""
Mensajero y social — réplica literal (fkengine.messenger.*, social.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    Messenger            — el mensajero (chat privado entre jugadores)
    MessengerAddress     — direccion (jugador)
    MessengerConversation — conversacion
    MessengerConversationMessage — mensaje
    MessengerUser        — usuario
    MessengerUserList    — lista de usuarios
    ISocialManagerCallback — callback social
"""


class MessengerUser:
    """fkengine.messenger.MessengerUser — usuario del mensajero."""

    def __init__(self, user_id=0, name=""):
        self.id = user_id
        self.name = name
        self.online = False


class MessengerAddress:
    """fkengine.messenger.MessengerAddress — direccion (jugador)."""

    def __init__(self, user_id=0):
        self.user_id = user_id


class MessengerConversationMessage:
    """Mensaje de conversacion."""

    def __init__(self, sender_id=0, text="", ts=0.0):
        self.sender_id = sender_id
        self.text = text
        self.ts = ts


class MessengerConversation:
    """fkengine.messenger.MessengerConversation — conversacion."""

    def __init__(self, peer=None):
        self.peer = peer
        self.messages = []

    def add(self, sender_id, text, ts=0.0):
        self.messages.append(MessengerConversationMessage(sender_id, text, ts))


class MessengerUserList:
    """Lista de usuarios."""

    def __init__(self):
        self.users = {}

    def add(self, user):
        self.users[user.id] = user

    def get(self, user_id):
        return self.users.get(user_id)


class Messenger:
    """fkengine.messenger.Messenger — el mensajero."""

    def __init__(self):
        self.users = MessengerUserList()
        self.conversations = {}

    def register(self, user):
        self.users.add(user)

    def conversation(self, peer_id):
        if peer_id not in self.conversations:
            user = self.users.get(peer_id)
            self.conversations[peer_id] = MessengerConversation(user)
        return self.conversations[peer_id]


class ISocialManagerCallback:
    """fkengine.social.ISocialManagerCallback — callback social."""

    def on_friends_loaded(self, friends):
        pass

    def on_invite(self, data):
        pass
