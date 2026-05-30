"""Entry point for the MedVista backend.

Usage:
    python run.py                  # single worker (default, safe for in-memory sessions)
    python run.py --workers 4      # multi-worker (requires shared session store)
"""
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="MedVista backend")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of uvicorn workers. "
                             "Note: >1 requires external session store (Redis/DB) "
                             "since in-memory sessions are per-process.")
    parser.add_argument("--http", default="h11",
                        choices=["h11", "httptools", "h2"],
                        help="HTTP protocol: h11 (default), httptools, or h2 (HTTP/2)")
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info",
        http=args.http,
    )


if __name__ == "__main__":
    main()
