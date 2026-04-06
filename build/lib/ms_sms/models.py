"""
Modèles de données du plugin SMS.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SendMessageResult:
    """
    Représente la réponse de l'API en cas de succès.

    Attributs :
        success      : True si l'envoi a réussi
        message      : Message retourné par l'API
        timestamp    : Timestamp Unix en ms
        type         : Type de message (ex: "SMS")
        phone_number : Numéro du destinataire formaté (ex: "+33634058195")
        raw          : Dict JSON complet de la réponse
    """

    success: bool
    message: str
    timestamp: int
    type: str
    phone_number: str
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict) -> "SendMessageResult":
        """Construit un SendMessageResult depuis un dict JSON."""
        return cls(
            success=data.get("success", False),
            message=data.get("message", ""),
            timestamp=data.get("timestamp", 0),
            type=data.get("type", ""),
            phone_number=data.get("phoneNumber", ""),
            raw=data,
        )

    @property
    def sent_at(self) -> str:
        """Timestamp Unix (ms) converti en date lisible."""
        if self.timestamp:
            dt = datetime.fromtimestamp(self.timestamp / 1000)
            return dt.strftime("%d/%m/%Y %H:%M:%S")
        return "—"

    def __str__(self) -> str:
        return (
            f"✅ Succès\n"
            f"  Message    : {self.message}\n"
            f"  Téléphone  : {self.phone_number}\n"
            f"  Type       : {self.type}\n"
            f"  Envoyé le  : {self.sent_at}"
        )
