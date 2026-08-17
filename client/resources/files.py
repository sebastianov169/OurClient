"""
Sistema de archivos del binario — réplica literal (fkengine.file.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    NativeFileManager   — gestor de archivos nativo
    NativeFile          — archivo nativo
    FileStream          — flujo de archivo
    FileSystem          — filesystem
    ByteArrayWrapper    — wrapper de byte array
    ZipEntry / Reader   — lectura de ZIP (los assets vienen en zip)
    ExtraField          — campo extra del zip
    StreamArchiveLoader — cargador de archivos (streaming)
    StreamFilesystemLoader — cargador de filesystem
"""

import struct
import zlib


class ByteArrayWrapper:
    """fkengine.file.native.ByteArrayWrapper — lectura/escritura de bytes."""

    def __init__(self, data=b""):
        self.data = bytearray(data)
        self.pos = 0

    def read_u8(self):
        v = self.data[self.pos]
        self.pos += 1
        return v

    def read_u16(self):
        v = struct.unpack_from(">H", self.data, self.pos)[0]
        self.pos += 2
        return v

    def read_u32(self):
        v = struct.unpack_from(">I", self.data, self.pos)[0]
        self.pos += 4
        return v

    def read_bytes(self, n):
        v = bytes(self.data[self.pos:self.pos + n])
        self.pos += n
        return v

    def write_u8(self, v):
        self.data.append(v & 0xFF)

    def write_u16(self, v):
        self.data += bytearray(struct.pack(">H", v))

    def write_u32(self, v):
        self.data += bytearray(struct.pack(">I", v))

    def write_bytes(self, b):
        self.data += bytearray(b)

    def remaining(self):
        return len(self.data) - self.pos


class NativeFile:
    """fkengine.file.native.NativeFile — archivo nativo."""

    def __init__(self, path=""):
        self.path = path
        self.data = None

    def read(self):
        with open(self.path, "rb") as fh:
            self.data = fh.read()
        return self.data

    def write(self, data):
        self.data = data
        with open(self.path, "wb") as fh:
            fh.write(data)


class FileStream:
    """fkengine.file.native.FileStream — flujo de archivo."""

    def __init__(self, path=""):
        self.path = path
        self.pos = 0

    def open(self, path):
        self.path = path
        self.pos = 0

    def read_bytes(self, n):
        with open(self.path, "rb") as fh:
            fh.seek(self.pos)
            data = fh.read(n)
            self.pos = fh.tell()
        return data


class FileSystem:
    """fkengine.file.native.FileSystem — operaciones de filesystem."""

    @staticmethod
    def exists(path):
        import os
        return os.path.exists(path)

    @staticmethod
    def list_dir(path):
        import os
        try:
            return os.listdir(path)
        except OSError:
            return []


class NativeFileManager:
    """fkengine.file.native.NativeFileManager — gestor de archivos."""

    def __init__(self):
        self.cache = {}

    def read(self, path):
        if path not in self.cache:
            f = NativeFile(path)
            self.cache[path] = f.read()
        return self.cache[path]


class ZipEntry:
    """fkengine.file.native.ZipEntry — entrada de zip."""

    def __init__(self, name="", data=b""):
        self.name = name
        self.data = data


class Reader:
    """fkengine.file.zip.Reader — lector de ZIP (assets del juego)."""

    def __init__(self):
        self.entries = {}

    def read(self, zip_data):
        """Lee un ZIP simple (firma PK + entradas sin comprimir/comprimidas)."""
        pos = 0
        n = len(zip_data)
        self.entries = {}
        while pos + 4 <= n:
            if zip_data[pos:pos + 4] != b"PK\x03\x04":
                break
            pos += 4
            (ver, flag, method, mtime, mdate, crc, csize, usize,
             nlen, elen) = struct.unpack_from("<HHHHHIIIHH", zip_data, pos)
            pos += 26
            name = zip_data[pos:pos + nlen].decode("utf-8", "replace")
            pos += nlen + elen
            data = zip_data[pos:pos + csize]
            pos += csize
            if method == 8:  # deflate (flujo zlib con header 0x78)
                data = zlib.decompress(data)
            self.entries[name] = data
        return self.entries

    def get(self, name):
        return self.entries.get(name)


class ExtraField:
    """fkengine.file.zip.ExtraField — campo extra del zip."""

    def __init__(self, tag=0, data=b""):
        self.tag = tag
        self.data = data


class StreamArchiveLoader:
    """fkengine.file.native.StreamArchiveLoader — carga por streaming."""

    def __init__(self):
        self.loaded = {}

    def load(self, archive, entry):
        if archive not in self.loaded:
            self.loaded[archive] = {}
        return self.loaded[archive].get(entry)


class StreamFilesystemLoader:
    """fkengine.file.native.StreamFilesystemLoader — carga del filesystem."""

    def __init__(self):
        self.cache = {}

    def load(self, path):
        if path not in self.cache:
            f = NativeFile(path)
            self.cache[path] = f.read()
        return self.cache[path]
