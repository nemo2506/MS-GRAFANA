"""
ms_sms — Client Python pour l'endpoint /api/send-message.

Usage rapide :
    from ms_sms import MessagePlugin, APIError

    plugin = MessagePlugin(
        base_url="https://monapi.com",
        bearer_token="mon_token",
        sender_id="MonApp",        # optionnel
    )

    # SMS simple
    result = plugin.send(recipient="0634058195", text="Bonjour !")
    print(result)

    # SMS + image JPEG
    result = plugin.send(
        recipient="0634058195",
        text="Voici une photo",
        image_path="photo.jpg",
    )

    # Gestion des erreurs
    try:
        result = plugin.send(recipient="0634058195", text="Test")
    except APIError as e:
        print(e.error)   # message d'erreur de l'API
        print(e.code)    # code applicatif (ou None)
        print(e.status)  # code HTTP
        print(e.raw)     # dict JSON complet
"""

from .client import MessagePlugin
from .exceptions import APIError
from .models import SendMessageResult

__all__ = ["MessagePlugin", "APIError", "SendMessageResult"]
__version__ = "1.0.0"
