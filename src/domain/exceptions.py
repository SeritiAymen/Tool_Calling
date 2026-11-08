class LLMError(Exception):
    """Erreur de base pour les appels LLM."""

class LLMTransientError(LLMError):
    """Erreur pouvant justifier un nouvel essai."""

class LLMFatalError(LLMError):
    """Erreur bloquante ou réponse inexploitable."""

