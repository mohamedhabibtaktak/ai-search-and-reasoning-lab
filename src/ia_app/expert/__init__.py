from .backward import backward_chaining
from .forward import forward_chaining
from .inference import InferenceResult, TraceEvent
from .models import KnowledgeBase, Rule, normalize_fact, parse_rule

__all__ = [
    "InferenceResult", "KnowledgeBase", "Rule", "TraceEvent",
    "backward_chaining", "forward_chaining", "normalize_fact", "parse_rule",
]
