"""
Base de datos y tienda — réplica literal (fkengine.db.*, fkengine.store.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    DatabaseManager     — gestor de BD local (SQLite? cache)
    ISModel             — modelo
    MultiSort           — orden multiple
    LocaleTbl           — tabla de locales
    ShaderCacheTbl      — cache de shaders
    StaticFilesTbl      — archivos estaticos
    IStoreReceiver      — receptor de la tienda
"""


class ISModel:
    """fkengine.db.ISModel — modelo de datos."""

    def __init__(self):
        self.fields = {}

    def get(self, key):
        return self.fields.get(key)

    def set(self, key, value):
        self.fields[key] = value


class MultiSort:
    """fkengine.db.MultiSort — orden multiple."""

    def __init__(self, keys=()):
        self.keys = list(keys)

    def sort(self, items):
        for key in reversed(self.keys):
            items.sort(key=lambda x: x.get(key, 0))
        return items


class LocaleTbl(ISModel):
    """Tabla de locales (traducciones)."""

    def __init__(self):
        super().__init__()
        self.locale = "es"
        self.strings = {}

    def translate(self, key):
        return self.strings.get(key, key)


class ShaderCacheTbl(ISModel):
    """Cache de shaders."""

    def __init__(self):
        super().__init__()
        self.cache = {}


class StaticFilesTbl(ISModel):
    """Archivos estaticos."""

    def __init__(self):
        super().__init__()
        self.files = {}


class DatabaseManager:
    """fkengine.db.DatabaseManager — gestor de BD."""

    def __init__(self):
        self.tables = {}

    def register(self, name, table):
        self.tables[name] = table

    def get(self, name):
        return self.tables.get(name)


class IStoreReceiver:
    """fkengine.store.IStoreReceiver — receptor de la tienda."""

    def __init__(self):
        self.on_purchase = None

    def purchase_complete(self, product_id):
        if self.on_purchase:
            self.on_purchase(product_id)
