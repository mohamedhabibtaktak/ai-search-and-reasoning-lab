"""Base de connaissances d'exemple : identification d'un animal."""
from __future__ import annotations

from .models import KnowledgeBase


def animal_kb() -> KnowledgeBase:
    kb = KnowledgeBase(facts=["poils", "mange_viande", "couleur_fauve", "taches_sombres"])
    for conditions, conclusion in [
        (["poils"], "mammifere"),
        (["allaite"], "mammifere"),
        (["plumes"], "oiseau"),
        (["pond_des_oeufs", "vole"], "oiseau"),
        (["mammifere", "mange_viande"], "carnivore"),
        (["mammifere", "dents_pointues", "griffes", "yeux_avant"], "carnivore"),
        (["mammifere", "sabots"], "ongule"),
        (["mammifere", "rumine"], "ongule"),
        (["carnivore", "couleur_fauve", "taches_sombres"], "guepard"),
        (["carnivore", "couleur_fauve", "rayures_noires"], "tigre"),
        (["ongule", "longues_pattes", "long_cou", "taches_sombres"], "girafe"),
        (["ongule", "rayures_noires"], "zebre"),
        (["oiseau", "ne_vole_pas", "long_cou", "longues_pattes", "noir_et_blanc"], "autruche"),
    ]:
        kb.add_rule(conditions, conclusion)
    return kb
