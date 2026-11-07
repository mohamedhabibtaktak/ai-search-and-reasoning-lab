"""Lecture / écriture JSON sûres (écriture atomique, messages lisibles)."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .errors import StorageError


def save_json(path: str | os.PathLike[str], data: dict[str, Any]) -> Path:
    target = Path(path)
    tmp = target.with_name(target.name + ".tmp")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, target)  # atomique : jamais de fichier à moitié écrit
    except OSError as exc:
        raise StorageError(f"Impossible d'écrire « {target} » : {exc.strerror or exc}") from exc
    return target


def load_json(path: str | os.PathLike[str]) -> dict[str, Any]:
    source = Path(path)
    try:
        raw = source.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise StorageError(f"Fichier introuvable : « {source} ».") from None
    except (OSError, UnicodeDecodeError) as exc:
        raise StorageError(f"Impossible de lire « {source} » : {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StorageError(f"JSON invalide dans « {source} » (ligne {exc.lineno}) : {exc.msg}.") from exc
    if not isinstance(data, dict):
        raise StorageError(f"« {source} » doit contenir un objet JSON.")
    return data
