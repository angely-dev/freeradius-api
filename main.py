#!/usr/bin/env python3

import argparse
import sys

import uvicorn

from src.api import app
from src.config import AppSettings

settings = AppSettings()


def create_parser():
    parser = argparse.ArgumentParser(
        description="FreeRADIUS API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Log level (default: info)"
    )
    
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    print(f"Starting FreeRADIUS API server on {args.host}:{args.port}")
    print(f"API documentation available at http://{args.host}:{args.port}/docs")
    
    try:
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)


if __name__ == "__main__":
    main()