#!/usr/bin/env python3
# AI Joke Generator - Powered by Ollama

import sys


def check_deps():
    missing = []
    for pkg, name in [("requests", "requests"), ("gtts", "gtts"), ("dotenv", "python-dotenv")]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(name)

    if missing:
        print("Missing packages:", ", ".join(missing))
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    return True


def check_ollama():
    try:
        import requests
        return requests.get("http://localhost:11434/api/tags", timeout=2).status_code == 200
    except Exception:
        return False


def main():
    print("\n  AI Joke Generator v1.0")
    print("  Powered by Ollama\n")

    if not check_deps():
        return 1

    if not check_ollama():
        print("  Ollama not running. Start with: ollama serve")
        print("  You can still launch the app and connect later.\n")

    try:
        from gui import run_app
        run_app()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
