#!/usr/bin/env python3
"""Direct launcher for the PROTCTR webapp."""

from __future__ import annotations

import socket

import uvicorn


def _find_free_port(start_port: int = 8000, attempts: int = 25) -> int:
    for port in range(start_port, start_port + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if sock.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No free port found in range {start_port}-{start_port + attempts - 1}")


def main() -> None:
    port = _find_free_port()
    print(f"PROTCTR webapp listening on http://127.0.0.1:{port}")
    uvicorn.run("webapp.main:app", host="127.0.0.1", port=port, reload=False)


if __name__ == "__main__":
    main()
