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
        self._trace: list[dict] = []

    def _extra(self, layer: str) -> dict:
        return {"request_id": self.request_id, "layer": layer}

    def start(self, layer: str):
        self._timings[layer] = time.perf_counter()
        _logger.info("started", extra=self._extra(layer))
        self._trace.append({"layer": layer, "action": "start"})

    def end(self, layer: str, status: str = "ok", detail: str = "") -> int:
        elapsed_ms = int((time.perf_counter() - self._timings.get(layer, time.perf_counter())) * 1000)
        _logger.info(f"completed {elapsed_ms}ms status={status} {detail}".strip(), extra=self._extra(layer))
        self._trace.append({"layer": layer, "action": "end", "elapsed_ms": elapsed_ms, "status": status, "detail": detail})
        return elapsed_ms

    def data(self, layer: str, title: str, payload: dict | list | str):
        import json
        if isinstance(payload, (dict, list)):
            dump = json.dumps(payload, indent=2, default=str)
        else:
            dump = str(payload)
        
        # Print legibly to terminal
        print(f"\n--- [LAYER OUTPUT: {layer} | {title}] ---")
        print(dump)
        print("-" * 50 + "\n")
        
        self._trace.append({"layer": layer, "action": "data", "title": title, "payload": payload})

    def get_trace(self) -> list[dict]:
        return self._trace

    def error(self, layer: str, message: str):
        _logger.error(f"ERROR: {message}", extra=self._extra(layer))
