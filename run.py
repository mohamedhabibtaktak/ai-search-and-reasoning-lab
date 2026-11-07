"""Lancement sans installation : python run.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from ia_app.cli.main import main  # noqa: E402

raise SystemExit(main())
