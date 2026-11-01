"""웹 UI 실행: `python web.py [--host 0.0.0.0] [--port 8000]` (CLI 는 main.py)."""
import argparse

import uvicorn

from vocal_similarity.webapp.app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Advanced Vocal Similarity Web UI")
    parser.add_argument("--host", default="127.0.0.1", help="바인딩 주소 (외부 접속 허용 시 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    shown_host = "localhost" if args.host in ("0.0.0.0", "127.0.0.1") else args.host
    print(f"[*] Web UI: http://{shown_host}:{args.port}")
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
