"""
Chat del binario — réplica literal (fkengine.game.chat.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    InGameChat        — el chat del juego (IRC talk003/UserGate en capturas)
    InGameChatMessage — un mensaje
    InGameChatBalloon — globo sobre la celula (ya en gameplay/input_chat.py)
"""


class InGameChatMessage:
    """fkengine.game.chat.InGameChatMessage — un mensaje del chat."""

    def __init__(self, sender="", text="", ts=0.0, color=(255, 255, 255)):
        self.sender = sender
        self.text = text
        self.ts = ts
        self.color = color


class InGameChat:
    """fkengine.game.chat.InGameChat — el chat en juego."""

    def __init__(self, max_messages=50):
        self.messages = []
        self.max_messages = max_messages
        self.visible = True

    def add(self, sender, text, color=(255, 255, 255)):
        self.messages.append(InGameChatMessage(sender, text, 0.0, color))
        if len(self.messages) > self.max_messages:
            del self.messages[:-self.max_messages]

    def clear(self):
        self.messages = []
