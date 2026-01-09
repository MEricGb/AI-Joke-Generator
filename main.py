#!/usr/bin/env python3
"""
AI Joke Generator - Main Entry Point (Ollama Version)

A Python desktop application that generates context-aware jokes using
Ollama (local LLM). Features text processing, text-to-speech, and
an intuitive graphical interface.

Usage:
    python main.py

Requirements:
    - Python 3.9+
    - Ollama installed and running (ollama serve)
    - Model pulled (ollama pull llama3.2)
"""

import sys


def check_dependencies() -> bool:
    """Check if all required dependencies are installed."""
    missing = []

    try:
        import requests
    except ImportError:
        missing.append("requests")

    try:
        import gtts
    except ImportError:
        missing.append("gtts")

    try:
        import dotenv
    except ImportError:
        missing.append("python-dotenv")

    if missing:
        print("Missing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstall them with:")
        print(f"  pip install {' '.join(missing)}")
        return False

    return True


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def print_banner() -> None:
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║           AI JOKE GENERATOR v1.0.0                    ║
    ║        Powered by Ollama (Local LLM)                  ║
    ╠═══════════════════════════════════════════════════════╣
    ║  Features:                                            ║
    ║  • AI-powered joke generation (Ollama)                ║
    ║  • Text signal processing & analysis                  ║
    ║  • Text-to-Speech (gTTS)                              ║
    ║  • Multi-language support (EN/RO)                     ║
    ╚═══════════════════════════════════════════════════════╝
    """
    print(banner)


def main() -> int:
    """Main entry point."""
    print_banner()

    # Check dependencies
    print("Checking dependencies...")
    if not check_dependencies():
        return 1
    print("All dependencies found!")

    # Check Ollama
    print("Checking Ollama...")
    if not check_ollama():
        print("\n⚠️  Ollama is not running!")
        print("Start it with:")
        print("  ollama serve")
        print("\nThen pull a model:")
        print("  ollama pull llama3.2")
        print("\nYou can still start the app and connect later.\n")
    else:
        print("Ollama is running!")

    # Start the application
    print("Starting application...\n")

    try:
        from gui import run_app
        run_app()
        return 0

    except KeyboardInterrupt:
        print("\nApplication interrupted.")
        return 0

    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
