"""
OurClient/engine.py — fkengine.core.Engine replicado.

El main loop del binario (FUN_140795df0): fixed-timestep 16.66ms,
acumulador, tick de los sistemas. Independiente del visor.
"""
import time


class Engine:
    """fkengine.core.Engine — main loop del cliente.

    Replica el game loop del binario (FUN_140795df0):
      dt_ms = clamp(now_ms - prev_ms, 0, 83.33)
      acumulador += dt_ms
      ticks de red consumidos de 16.66ms
    """

    TICK_MS = 16.666666666666668

    def __init__(self, on_tick=None, fps=60):
        self.on_tick = on_tick          # callback(dt_segundos) cada frame
        self.fps = fps
        self.running = False
        self.frame = 0
        self._prev_ms = None
        self._accum_ms = 0.0
        self._last_render = 0.0

    def start(self):
        self.running = True
        self._prev_ms = time.time() * 1000.0
        self._last_render = time.time()

    def stop(self):
        self.running = False

    def step(self):
        """Un frame: avanza el acumulador de ticks y llama on_tick."""
        now_ms = time.time() * 1000.0
        dt_ms = min(max(now_ms - self._prev_ms, 0.0), 83.33333333333334)
        self._prev_ms = now_ms
        self._accum_ms += dt_ms
        self.frame += 1
        if self.on_tick:
            self.on_tick(dt_ms / 1000.0)
        return dt_ms / 1000.0

    def run(self, max_frames=None):
        """Loop completo (bloqueante) — el while running del binario."""
        self.start()
        import time as _t
        target = 1.0 / self.fps
        while self.running:
            t0 = _t.time()
            self.step()
            elapsed = _t.time() - t0
            if elapsed < target:
                _t.sleep(target - elapsed)
            if max_frames and self.frame >= max_frames:
                self.running = False
        self.stop()
