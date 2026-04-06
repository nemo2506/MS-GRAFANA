"""
Interface en ligne de commande du plugin SMS.
Installée automatiquement en tant que commande `ms-sms-send` via setup.py.
"""

import argparse
import sys

import requests

from .client import MessagePlugin
from .exceptions import APIError


def main():
    parser = argparse.ArgumentParser(
        prog="ms-sms-send",
        description="Envoie un SMS via /api/send-message",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
  ms-sms-send --url https://monapi.com --token montoken \\
           --recipient 0634058195 --text "Bonjour !"

  ms-sms-send --url https://monapi.com --token montoken \\
           --recipient 0634058195 --text "Photo :" --image photo.jpg
        """,
    )

    parser.add_argument(
        "--url", required=True,
        help="URL de base de l'API (ex: https://monapi.com)"
    )
    parser.add_argument(
        "--token", required=True,
        help="Bearer token d'authentification"
    )
    parser.add_argument(
        "--recipient", required=True,
        help="Numéro du destinataire (ex: 0634058195)"
    )
    parser.add_argument(
        "--text", required=True,
        help="Texte du message SMS"
    )
    parser.add_argument(
        "--sender-id", default="",
        help="Identifiant de l'expéditeur - senderId (optionnel)"
    )
    parser.add_argument(
        "--image", default=None,
        metavar="FICHIER.jpg",
        help="Chemin vers un fichier JPEG à joindre (optionnel)"
    )
    parser.add_argument(
        "--timeout", type=int, default=30,
        help="Timeout HTTP en secondes (défaut: 30)"
    )

    args = parser.parse_args()

    plugin = MessagePlugin(
        base_url=args.url,
        bearer_token=args.token,
        sender_id=args.sender_id,
        timeout=args.timeout,
    )

    try:
        result = plugin.send(
            recipient=args.recipient,
            text=args.text,
            image_path=args.image,
        )
        print(result)
        sys.exit(0)

    except FileNotFoundError as e:
        print(f"❌ Fichier introuvable : {e}", file=sys.stderr)
        sys.exit(2)
    except TypeError as e:
        print(f"❌ Type de fichier invalide : {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"❌ Paramètre invalide : {e}", file=sys.stderr)
        sys.exit(2)
    except APIError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    except requests.Timeout:
        print(
            f"❌ Timeout : le serveur n'a pas répondu en {args.timeout}s.",
            file=sys.stderr,
        )
        sys.exit(1)
    except requests.ConnectionError:
        print(
            f"❌ Connexion impossible : {args.url}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
