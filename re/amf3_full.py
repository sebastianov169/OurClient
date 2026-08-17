#!/usr/bin/env python3
"""amf3_full.py - Decoder AMF3 COMPLETO (objetos, arrays asociativos, dicts,
vectores) para el wire de MitosisOG. El Amf3Decoder de tcp_full.py no soporta
markers de objeto (0x0A) ni arrays asociativos: pierde los dicts de info de
jugador (username/name) que llegan en el op 16. Este decoder los recupera."""
import struct

class Amf3Decoder:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.string_refs = []
        self.obj_refs = []
        self.trait_refs = []

    def read_u8(self):
        if self.pos >= len(self.data):
            raise Exception("AMF3 end at %d" % self.pos)
        b = self.data[self.pos]
        self.pos += 1
        return b

    def read_bytes(self, n):
        out = self.data[self.pos:self.pos + n]
        self.pos += n
        return out

    def read_u29(self):
        result = 0
        for i in range(4):
            b = self.read_u8()
            if i < 3:
                result = (result << 7) | (b & 0x7F)
                if not (b & 0x80):
                    return result
            else:
                return (result << 8) | b
        return result

    def read_double(self):
        return struct.unpack('>d', self.read_bytes(8))[0]

    def read_string_data(self):
        handle = self.read_u29()
        if not (handle & 1):
            idx = handle >> 1
            return self.string_refs[idx] if 0 <= idx < len(self.string_refs) else ""
        length = handle >> 1
        if length == 0:
            return ""
        text = self.read_bytes(length).decode('utf-8', errors='replace')
        self.string_refs.append(text)
        return text

    def read_value(self):
        marker = self.read_u8()
        if marker == 0x00:
            return "undefined"
        if marker == 0x01:
            return None
        if marker == 0x02:
            return False
        if marker == 0x03:
            return True
        if marker == 0x04:
            v = self.read_u29()
            if v & 0x10000000:
                v -= 0x20000000
            return v
        if marker == 0x05:
            return self.read_double()
        if marker == 0x06:
            return self.read_string_data()
        if marker == 0x07:      # XMLDoc
            h = self.read_u29()
            if not (h & 1):
                return "<xml-ref>"
            return self.read_bytes(h >> 1).decode('utf-8', errors='replace')
        if marker == 0x08:      # Date
            h = self.read_u29()
            if not (h & 1):
                return 0.0
            return self.read_double()
        if marker == 0x09:
            return self.read_array()
        if marker == 0x0A:
            return self.read_object()
        if marker == 0x0B:      # XML
            h = self.read_u29()
            if not (h & 1):
                return "<xml-ref>"
            return self.read_bytes(h >> 1).decode('utf-8', errors='replace')
        if marker == 0x0C:      # ByteArray
            h = self.read_u29()
            if not (h & 1):
                return b""
            return self.read_bytes(h >> 1)
        if marker == 0x0D:      # Vector<int>
            return self.read_vector("i")
        if marker == 0x0E:      # Vector<uint>
            return self.read_vector("u")
        if marker == 0x0F:      # Vector<double>
            return self.read_vector("d")
        if marker == 0x10:      # Vector<object>
            return self.read_vector("o")
        if marker == 0x11:      # Dictionary
            return self.read_dictionary()
        raise Exception("unsupported AMF3 marker: 0x%02x @%d" % (marker, self.pos))

    def read_array(self):
        """Array AMF3: parte asociativa (dict) + parte densa (lista).
        Devuelve dict si hay claves asociativas, si no la lista densa."""
        handle = self.read_u29()
        if not (handle & 1):
            idx = handle >> 1
            return self.obj_refs[idx] if 0 <= idx < len(self.obj_refs) else []
        dense_count = handle >> 1
        assoc = {}
        while True:
            key = self.read_string_data()
            if not key:
                break
            assoc[key] = self.read_value()
        dense = [self.read_value() for _ in range(dense_count)]
        if assoc:
            assoc["_dense"] = dense
            return assoc
        return dense

    def read_traits(self):
        """Traits de objeto AMF3: devuelve (class_name, sealed, dynamic)."""
        handle = self.read_u29()
        if not (handle & 1):
            idx = handle >> 1
            return self.trait_refs[idx] if 0 <= idx < len(self.trait_refs) else ("", [], False)
        externalizable = bool(handle & 0x02)
        dynamic = bool(handle & 0x04)
        count = handle >> 3
        class_name = self.read_string_data()
        sealed = [self.read_string_data() for _ in range(count)]
        trait = (class_name, sealed, dynamic)
        self.trait_refs.append(trait)
        return trait

    def read_object(self):
        """Objeto AMF3 (marker 0x0A): traits + valores sealed + dynamic."""
        handle = self.read_u29()
        if not (handle & 1):
            idx = handle >> 1
            return self.obj_refs[idx] if 0 <= idx < len(self.obj_refs) else {}
        class_name, sealed, dynamic = self.read_traits()
        obj = {"__class__": class_name} if class_name else {}
        for name in sealed:
            obj[name] = self.read_value()
        if dynamic:
            while True:
                key = self.read_string_data()
                if not key:
                    break
                obj[key] = self.read_value()
        self.obj_refs.append(obj)
        return obj

    def read_vector(self, kind):
        handle = self.read_u29()
        if not (handle & 1):
            idx = handle >> 1
            return self.obj_refs[idx] if 0 <= idx < len(self.obj_refs) else []
        count = handle >> 1
        self.read_u8()  # fixed flag
        out = []
        if kind == "i":
            out = list(struct.unpack(">%di" % count, self.read_bytes(4 * count)))
        elif kind == "u":
            out = list(struct.unpack(">%dI" % count, self.read_bytes(4 * count)))
        elif kind == "d":
            out = list(struct.unpack(">%dd" % count, self.read_bytes(8 * count)))
        else:
            out = [self.read_value() for _ in range(count)]
        self.obj_refs.append(out)
        return out

    def read_dictionary(self):
        handle = self.read_u29()
        if not (handle & 1):
            idx = handle >> 1
            return self.obj_refs[idx] if 0 <= idx < len(self.obj_refs) else {}
        count = handle >> 1
        self.read_u8()  # weak keys flag
        out = {}
        for _ in range(count):
            k = self.read_value()
            v = self.read_value()
            out[str(k)] = v
        self.obj_refs.append(out)
        return out
