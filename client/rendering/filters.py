"""
Filtros del binario — réplica literal (fkengine.filters.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    FilterBase        — filtro base
    BlurFilter        — desenfoque
    FilterManager     — gestor de filtros
    ProgressMapFilter — filtro de mapa de progreso (starling)
    CircleBuffer      — buffer de circulos (render batch)
"""


class FilterBase:
    """fkengine.filters.base.FilterBase — filtro base."""

    def __init__(self):
        self.enabled = False
        self.intensity = 1.0

    def apply(self, surf):
        """Aplica el filtro (no-op base)."""
        return surf


class BlurFilter(FilterBase):
    """fkengine.filters.blur.BlurFilter — desenfoque."""

    def __init__(self, radius=1.0):
        super().__init__()
        self.radius = radius


class FilterManager:
    """fkengine.filters.manager.FilterManager — gestiona filtros."""

    def __init__(self):
        self.filters = []

    def add(self, filt):
        self.filters.append(filt)

    def apply_all(self, surf):
        for f in self.filters:
            if f.enabled:
                surf = f.apply(surf)
        return surf


class ProgressMapFilter(FilterBase):
    """fkengine.filters.starling.ProgressMapFilter — filtro de progreso."""

    def __init__(self, progress=0.0):
        super().__init__()
        self.progress = progress


class CircleBuffer:
    """fkengine.geometries.CircleBuffer — buffer de circulos (GPU)."""

    def __init__(self, capacity=1024):
        self.capacity = capacity
        self.data = []

    def add(self, x, y, radius, color):
        if len(self.data) < self.capacity:
            self.data.append((x, y, radius, color))

    def clear(self):
        self.data = []
