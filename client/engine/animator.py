"""
Animador del binario — réplica literal (fkengine.animator.*).

Fuente: Ghidra MCP, re/_bulk/ (classregs decompilados).

    Animator2D              — animador 2D (posicion/escala/alpha)
    AnimatorFunction        — funcion de easing base
    AnimatorFunctionLinear  — easing lineal
    AnimatorFunctionEaseIn  — ease-in
    AnimatorFunctionEaseOut — ease-out
    AnimatorFunctionSwing   — swing
    Node                    — nodo de animacion
    Spline / Spline3D       — splines
"""

import math


class AnimatorFunction:
    """Funcion de easing base."""

    def apply(self, t):
        return t


class AnimatorFunctionLinear(AnimatorFunction):
    def apply(self, t):
        return t


class AnimatorFunctionEaseIn(AnimatorFunction):
    def apply(self, t):
        return t * t


class AnimatorFunctionEaseOut(AnimatorFunction):
    def apply(self, t):
        return 1.0 - (1.0 - t) * (1.0 - t)


class AnimatorFunctionSwing(AnimatorFunction):
    def apply(self, t):
        return 0.5 - 0.5 * math.cos(math.pi * t)


class Node:
    """Nodo de animacion (objetivo + propiedades)."""

    def __init__(self, target=None, duration=1.0, easing=None):
        self.target = target
        self.duration = duration
        self.easing = easing or AnimatorFunctionLinear()
        self.elapsed = 0.0
        self.from_values = {}
        self.to_values = {}
        self.complete = False

    def tick(self, dt):
        if self.complete:
            return
        self.elapsed += dt
        t = min(1.0, self.elapsed / self.duration) if self.duration > 0 else 1.0
        e = self.easing.apply(t)
        if self.target is not None:
            for key, to in self.to_values.items():
                frm = self.from_values.get(key, to)
                setattr(self.target, key, frm + (to - frm) * e)
        if t >= 1.0:
            self.complete = True


class Animator2D:
    """Animador 2D — anima posicion/escala/alpha de un objeto."""

    def __init__(self, target=None):
        self.target = target
        self.nodes = []

    def animate(self, to_values, duration=1.0, easing=None):
        node = Node(self.target, duration, easing)
        if self.target is not None:
            for key in to_values:
                node.from_values[key] = getattr(self.target, key, to_values[key])
        node.to_values = dict(to_values)
        self.nodes.append(node)
        return node

    def tick(self, dt):
        for node in self.nodes:
            node.tick(dt)
        self.nodes = [n for n in self.nodes if not n.complete]


class Spline:
    """Spline 2D (interpolacion por puntos)."""

    def __init__(self, points=()):
        self.points = list(points)

    def sample(self, t):
        if not self.points:
            return (0.0, 0.0)
        n = len(self.points)
        if n == 1:
            return self.points[0]
        t = max(0.0, min(0.999999, t))
        i = int(t * (n - 1))
        frac = t * (n - 1) - i
        p0, p1 = self.points[i], self.points[min(i + 1, n - 1)]
        return (p0[0] + (p1[0] - p0[0]) * frac,
                p0[1] + (p1[1] - p0[1]) * frac)


class Spline3D(Spline):
    """Spline 3D."""

    def sample(self, t):
        if not self.points:
            return (0.0, 0.0, 0.0)
        n = len(self.points)
        if n == 1:
            return self.points[0]
        t = max(0.0, min(0.999999, t))
        i = int(t * (n - 1))
        frac = t * (n - 1) - i
        p0, p1 = self.points[i], self.points[min(i + 1, n - 1)]
        return (p0[0] + (p1[0] - p0[0]) * frac,
                p0[1] + (p1[1] - p0[1]) * frac,
                p0[2] + (p1[2] - p0[2]) * frac)


class NodeHelper:
    """Utilidades de nodos."""

    @staticmethod
    def chain(*nodes):
        """Encadena nodos (uno tras otro)."""
        result = []
        for i, node in enumerate(nodes):
            if i > 0:
                prev = result[-1]
                orig = node.tick
                def chained(dt, orig=orig, prev=prev):
                    if not prev.complete:
                        return
                    orig(dt)
                node.tick = chained
            result.append(node)
        return result
