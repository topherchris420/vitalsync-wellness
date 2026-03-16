#!/usr/bin/env python3
"""
Tiny local SSE bridge for VitalSync.

Runs an HTTP server with:
- GET  /events  -> Server-Sent Events stream for browser subscribers
- POST /push    -> Push one sample or a list of samples
- GET  /health  -> Health check

Sample payloads for /push:
{"metric":"heartRate","value":71}
{"samples":[{"metric":"sleep","value":6.4},{"metric":"stress","value":48}]}
"""

from __future__ import annotations

import argparse
import json
import random
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Empty, Queue
from collections.abc import Iterable
from typing import Any


ALLOWED_METRICS = {"heartRate", "sleep", "stress"}
SUBSCRIBERS: set[Queue[str]] = set()
SUBSCRIBERS_LOCK = threading.Lock()


def clamp(metric: str, value: float) -> float:
    if metric == "heartRate":
        return max(35.0, min(210.0, value))
    if metric == "sleep":
        return max(0.0, min(16.0, value))
    if metric == "stress":
        return max(0.0, min(100.0, value))
    return value


def normalize_sample(metric: Any, value: Any) -> dict[str, Any] | None:
    if metric not in ALLOWED_METRICS:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    bounded = clamp(metric, numeric)
    if metric in {"heartRate", "stress"}:
        bounded = round(bounded)
    else:
        bounded = round(bounded, 2)
    return {"metric": metric, "value": bounded}


def extract_samples(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict) and "metric" in payload and "value" in payload:
        sample = normalize_sample(payload["metric"], payload["value"])
        return [sample] if sample else []

    if isinstance(payload, dict) and isinstance(payload.get("samples"), list):
        return extract_samples(payload["samples"])

    if isinstance(payload, list):
        normalized: list[dict[str, Any]] = []
        for item in payload:
            if isinstance(item, dict) and "metric" in item and "value" in item:
                sample = normalize_sample(item["metric"], item["value"])
                if sample:
                    normalized.append(sample)
        return normalized

    return []


def broadcast_samples(samples: Iterable[dict[str, Any]]) -> None:
    payload = {"samples": list(samples), "timestamp": time.time()}
    if not payload["samples"]:
        return

    serialized = json.dumps(payload, separators=(",", ":"))
    stale: list[Queue[str]] = []
    with SUBSCRIBERS_LOCK:
        for queue in list(SUBSCRIBERS):
            try:
                queue.put_nowait(serialized)
            except Exception:
                stale.append(queue)
        for queue in stale:
            SUBSCRIBERS.discard(queue)


class BridgeRequestHandler(BaseHTTPRequestHandler):
    server_version = "VitalSyncMetricBridge/1.0"

    def _set_common_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self._set_common_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._set_common_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, {"ok": True})
            return

        if self.path == "/events":
            self.handle_events()
            return

        self._send_json(
            HTTPStatus.OK,
            {
                "name": "VitalSync Metric Bridge",
                "endpoints": ["/events", "/push", "/health"],
            },
        )

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/push":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length > 0 else b""
        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid JSON"})
            return

        samples = extract_samples(payload)
        if not samples:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "No valid samples. Use metric/value or samples[] payload."},
            )
            return

        broadcast_samples(samples)
        self._send_json(HTTPStatus.OK, {"ok": True, "count": len(samples)})

    def handle_events(self) -> None:
        queue: Queue[str] = Queue(maxsize=256)
        with SUBSCRIBERS_LOCK:
            SUBSCRIBERS.add(queue)

        self.send_response(HTTPStatus.OK)
        self._set_common_headers()
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                try:
                    message = queue.get(timeout=15.0)
                    packet = f"data: {message}\n\n".encode("utf-8")
                except Empty:
                    packet = b": keepalive\n\n"
                self.wfile.write(packet)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with SUBSCRIBERS_LOCK:
                SUBSCRIBERS.discard(queue)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep output concise while still exposing requests.
        print(f"[bridge] {self.address_string()} - {fmt % args}")


def run_demo_loop(stop_event: threading.Event, interval: float) -> None:
    state = {"heartRate": 68.0, "sleep": 6.2, "stress": 50.0}
    metrics = ("heartRate", "sleep", "stress")

    while not stop_event.wait(interval):
        metric = random.choice(metrics)
        if metric == "heartRate":
            state[metric] = clamp(metric, state[metric] + random.uniform(-2.8, 2.8))
        elif metric == "sleep":
            state[metric] = clamp(metric, state[metric] + random.uniform(-0.12, 0.12))
        else:
            state[metric] = clamp(metric, state[metric] + random.uniform(-4.0, 4.0))
        sample = normalize_sample(metric, state[metric])
        if sample:
            broadcast_samples([sample])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VitalSync local metric bridge")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Demo sample interval in seconds",
    )
    parser.add_argument(
        "--no-demo",
        action="store_true",
        help="Disable synthetic demo metric stream",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), BridgeRequestHandler)
    stop_event = threading.Event()
    interval = max(0.2, args.interval)

    demo_thread: threading.Thread | None = None
    if not args.no_demo:
        demo_thread = threading.Thread(
            target=run_demo_loop,
            args=(stop_event, interval),
            daemon=True,
        )
        demo_thread.start()

    print(f"[bridge] Serving on http://{args.host}:{args.port}")
    print("[bridge] SSE endpoint: /events | Push endpoint: /push | Health: /health")
    if args.no_demo:
        print("[bridge] Demo stream disabled")
    else:
        print(f"[bridge] Demo stream enabled at {interval:.2f}s interval")

    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\n[bridge] Shutting down...")
    finally:
        stop_event.set()
        server.shutdown()
        server.server_close()
        if demo_thread and demo_thread.is_alive():
            demo_thread.join(timeout=1.0)


if __name__ == "__main__":
    main()
