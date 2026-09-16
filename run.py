#!/usr/bin/env python3
"""Start SETU on this machine.  python run.py  ->  http://127.0.0.1:8000"""
import os
import sys
import threading
import webbrowser

import uvicorn

PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "127.0.0.1")   # set HOST=0.0.0.0 to demo from a phone on the same wifi


def main():
    if "--reset" in sys.argv:
        from app import db
        db.init(force=True)
        print("Database reset and reseeded.")
    url = "http://127.0.0.1:%d" % PORT
    print("\n  SETU  |  SIH 2026  |  SIH26043  |  Team 6ixTitans")
    print("  Running at " + url + "   (Ctrl+C to stop)\n")
    if "--no-browser" not in sys.argv:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload="--reload" in sys.argv)


if __name__ == "__main__":
    main()
