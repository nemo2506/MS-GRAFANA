"""
Exceptions du plugin SMS.
"""

from datetime import datetime


class APIError(Exception):
    """
    Levée quand l'API retourne success=false ou un code HTTP d'erreur.

    Attributs :
        error     : Message d'erreur retourné par l'API
        code      : Code d'erreur applicatif (optionnel, ex: 404)
        timestamp : Timestamp Unix (ms) de l'erreur
        status    : Code HTTP de la réponse (0 si pas de réponse HTTP)
        raw       : Dict complet de la réponse JSON
    """

    def __init__(
        self,
        error: str,
        code: int = None,
        timestamp: int = 0,
        status: int = 0,
        raw: dict = None,
    ):
        self.error = error
        self.code = code
        self.timestamp = timestamp
        self.status = status
        self.raw = raw or {}
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        parts = [self.error]
        if self.code is not None:
            parts.append(f"code={self.code}")
        if self.status:
            parts.append(f"HTTP {self.status}")
        return " | ".join(parts)

    @property
    def sent_at(self) -> str:
        """Timestamp Unix (ms) converti en date lisible."""
        if self.timestamp:
            dt = datetime.fromtimestamp(self.timestamp / 1000)
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        return "—"

    def __str__(self) -> str:
        lines = [f"❌ Erreur API : {self.error}"]
        if self.code is not None:
            lines.append(f"  Code applicatif : {self.code}")
        if self.status:
            lines.append(f"  Code HTTP       : {self.status}")
        lines.append(f"  Timestamp       : {self.sent_at}")
        return "\n".join(lines)
