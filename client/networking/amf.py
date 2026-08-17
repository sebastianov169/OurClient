"""
AMF del binario — réplica literal (amf.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    AmfValue    — valor AMF (el serializador del protocolo)
    AmfVersion  — version AMF (3 = AMF3)
    ClassType   — tipo de clase
    ResultIndex — indice de resultado
    SenderVersion — version del emisor

NOTA: el visor ya tiene el decoder AMF3 completo en re/amf3_full.py
(verificado contra capturas reales: op16 nombres, op19 celulas). Esta
clase es el modelo del binario para el serializador.
"""

# tipos AMF3 (del decoder amf3_full.py, verificados)
AMF3_UNDEFINED = 0x00
AMF3_NULL = 0x01
AMF3_FALSE = 0x02
AMF3_TRUE = 0x03
AMF3_INTEGER = 0x04
AMF3_DOUBLE = 0x05
AMF3_STRING = 0x06
AMF3_XMLDOC = 0x07
AMF3_DATE = 0x08
AMF3_ARRAY = 0x09
AMF3_OBJECT = 0x0A
AMF3_XML = 0x0B
AMF3_BYTEARRAY = 0x0C
AMF3_VECTOR_INT = 0x0D
AMF3_VECTOR_UINT = 0x0E
AMF3_VECTOR_DOUBLE = 0x0F
AMF3_VECTOR_OBJECT = 0x10
AMF3_DICTIONARY = 0x11


class AmfVersion:
    """amf.AmfVersion — version AMF."""

    AMF0 = 0
    AMF3 = 3


class AmfValue:
    """amf.AmfValue — un valor AMF (tipo + datos)."""

    def __init__(self, type_=AMF3_UNDEFINED, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return "AmfValue(type=0x%02x, value=%r)" % (self.type, self.value)


class ClassType:
    """amf.ClassType — tipo de clase serializada."""

    def __init__(self, name="", dynamic=False, sealed=True):
        self.name = name
        self.dynamic = dynamic
        self.sealed = sealed


class ResultIndex:
    """amf.ResultIndex — indice de resultado (serializacion)."""

    def __init__(self, index=0):
        self.index = index


class SenderVersion:
    """amf.SenderVersion — version del emisor."""

    def __init__(self, version=3):
        self.version = version
