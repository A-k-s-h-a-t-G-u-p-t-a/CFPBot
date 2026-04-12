import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | req=%(request_id)s | layer=%(layer)s | %(message)s",
)
_logger = logging.getLogger("cfpbot")


class LayerLogger:
    def __init__(self, request_id: str):
        self.request_id = request_id
        self._timings: dict[str, float] = {}

    def _extra(self, layer: str) -> dict:
        return {"request_id": self.request_id, "layer": layer}

    def start(self, layer: str):
        self._timings[layer] = time.perf_counter()
        _logger.info("started", extra=self._extra(layer))

    def end(self, layer: str, status: str = "ok", detail: str = "") -> int:
        elapsed_ms = int((time.perf_counter() - self._timings.get(layer, time.perf_counter())) * 1000)
        _logger.info(f"completed {elapsed_ms}ms status={status} {detail}".strip(), extra=self._extra(layer))
        return elapsed_ms

    def error(self, layer: str, message: str):
        _logger.error(f"ERROR: {message}", extra=self._extra(layer))
