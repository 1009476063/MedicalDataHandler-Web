"""Entry point for the MedicalDataHandler backend.

Usage:
    python run.py                  # single worker (default, safe for in-memory sessions)
    python run.py --workers 4      # multi-worker (requires shared session store)
"""
import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="MedicalDataHandler backend")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of uvicorn workers. "
                             "Note: >1 requires external session store (Redis/DB) "
                             "since in-memory sessions are per-process.")
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main()
