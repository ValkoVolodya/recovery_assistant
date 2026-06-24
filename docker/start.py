import asyncio
import os
import socket
import sys
from urllib.parse import urlparse


async def wait_for_host(host: str, port: int, timeout_seconds: int = 60) -> None:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while True:
        try:
            socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            await writer.wait_closed()
            return
        except OSError as exc:
            if asyncio.get_running_loop().time() >= deadline:
                raise TimeoutError(f"Database host {host}:{port} did not become reachable: {exc}") from exc
            await asyncio.sleep(2)


async def main() -> None:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    parsed = urlparse(database_url)
    if parsed.hostname is None or parsed.port is None:
        raise RuntimeError("DATABASE_URL must include hostname and port")

    await wait_for_host(parsed.hostname, parsed.port)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise
