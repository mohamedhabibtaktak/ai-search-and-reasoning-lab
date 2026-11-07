"""Sauvegarde / chargement d'une base de connaissances (JSON)."""
from __future__ import annotations

from pathlib import Path

from ..common.jsonio import load_json, save_json
from .models import KnowledgeBase


def save_kb(kb: KnowledgeBase, path: str | Path) -> Path:
    return save_json(path, kb.to_dict())


def load_kb(path: str | Path) -> KnowledgeBase:
    return KnowledgeBase.from_dict(load_json(path))
