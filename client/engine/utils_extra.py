"""
Utils del binario (continuacion) — réplica literal (fkengine.utils.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    ArrayUtil       — utilidades de arrays
    AttributeParser — parser de atributos
    Defines         — defines del juego
"""


class ArrayUtil:
    """fkengine.utils.ArrayUtil — utilidades de arrays."""

    @staticmethod
    def remove(arr, item):
        if item in arr:
            arr.remove(item)
            return True
        return False

    @staticmethod
    def shuffle(arr, rng=None):
        import random
        if rng:
            random.shuffle(arr)
        else:
            random.shuffle(arr)
        return arr

    @staticmethod
    def unique(arr):
        seen = set()
        result = []
        for x in arr:
            if x not in seen:
                seen.add(x)
                result.append(x)
        return result


class AttributeParser:
    """fkengine.utils.AttributeParser — parser de atributos (XML/string)."""

    def __init__(self):
        self.attrs = {}

    def parse(self, text):
        """Parsea 'clave=valor clave2=valor2'."""
        self.attrs = {}
        for part in text.split():
            if "=" in part:
                k, v = part.split("=", 1)
                self.attrs[k] = v
        return self.attrs

    def get(self, key, default=None):
        return self.attrs.get(key, default)


class Defines:
    """fkengine.utils.Defines — defines del juego (constantes de compilacion)."""

    # los defines reales se rellenan en runtime por la config del server
    VALUES = {}

    @classmethod
    def get(cls, key, default=None):
        return cls.VALUES.get(key, default)

    @classmethod
    def set(cls, key, value):
        cls.VALUES[key] = value
