"""Hiérarchie d'erreurs métier : l'interface les affiche sans trace Python."""


class AppError(Exception):
    """Erreur attendue (saisie invalide, fichier illisible, ...)."""


class KnowledgeBaseError(AppError):
    """Fait ou règle invalide."""


class GraphError(AppError):
    """Graphe invalide (sommet inconnu, coût négatif, ...)."""


class MissingHeuristicError(GraphError):
    """Une heuristique h(n) manque pour un algorithme informé."""


class StorageError(AppError):
    """Lecture ou écriture de fichier impossible."""


class VisualizationUnavailable(AppError):
    """matplotlib n'est pas installé."""
