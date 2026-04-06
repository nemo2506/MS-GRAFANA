"""
Tests unitaires du plugin SMS.

Installation des dépendances de test :
    pip install -e ".[dev]"

Lancement :
    pytest tests/ -v
"""

import base64
import json
import pytest
import responses as resp_mock
import requests

from ms_sms import MessagePlugin, APIError, SendMessageResult

API_URL   = "https://monapi.com"
TOKEN     = "test_bearer_token"
ENDPOINT  = f"{API_URL}/api/send-message"
RECIPIENT = "0634058195"
TEXT      = "Bonjour depuis les tests !"


# -----------------------------------------------------------------------
# Fixture : plugin prêt à l'emploi
# -----------------------------------------------------------------------

@pytest.fixture
def plugin():
    return MessagePlugin(base_url=API_URL, bearer_token=TOKEN, sender_id="TestApp")


# -----------------------------------------------------------------------
# Réponses types
# -----------------------------------------------------------------------

SUCCESS_RESPONSE = {
    "success": True,
    "message": "✅ SMS envoyé avec succès vers +33634058195",
    "timestamp": 1775425870604,
    "type": "SMS",
    "phoneNumber": "+33634058195",
}

ERROR_404 = {
    "success": False,
    "error": "❌ Endpoint introuvable",
    "code": 404,
    "timestamp": 1775425918484,
}

ERROR_401 = {
    "success": False,
    "error": "❌ Requête non autorisée : jeton manquant ou invalide",
    "timestamp": 1775425983324,
}


# -----------------------------------------------------------------------
# Tests — cas nominal
# -----------------------------------------------------------------------

class TestSendSuccess:

    @resp_mock.activate
    def test_sms_simple(self, plugin):
        resp_mock.add(resp_mock.POST, ENDPOINT, json=SUCCESS_RESPONSE, status=200)

        result = plugin.send(recipient=RECIPIENT, text=TEXT)

        assert isinstance(result, SendMessageResult)
        assert result.success is True
        assert result.phone_number == "+33634058195"
        assert result.type == "SMS"
        assert result.sent_at != "—"

    @resp_mock.activate
    def test_payload_envoyé(self, plugin):
        """Vérifie que le corps POST est correctement construit."""
        resp_mock.add(resp_mock.POST, ENDPOINT, json=SUCCESS_RESPONSE, status=200)

        plugin.send(recipient=RECIPIENT, text=TEXT)

        sent = json.loads(resp_mock.calls[0].request.body)
        assert sent["senderId"]   == "TestApp"
        assert sent["recipient"]  == RECIPIENT
        assert sent["text"]       == TEXT
        assert sent["base64Jpeg"] == ""

    @resp_mock.activate
    def test_authorization_header(self, plugin):
        """Vérifie la présence du Bearer token dans les headers."""
        resp_mock.add(resp_mock.POST, ENDPOINT, json=SUCCESS_RESPONSE, status=200)

        plugin.send(recipient=RECIPIENT, text=TEXT)

        headers = resp_mock.calls[0].request.headers
        assert headers["Authorization"] == f"Bearer {TOKEN}"

    @resp_mock.activate
    def test_sms_avec_image(self, plugin, tmp_path):
        """Vérifie que l'image est correctement encodée en base64."""
        # Créer un faux JPEG
        img = tmp_path / "test.jpg"
        img.write_bytes(b"\xff\xd8\xff" + b"\x00" * 10)

        resp_mock.add(resp_mock.POST, ENDPOINT, json=SUCCESS_RESPONSE, status=200)

        result = plugin.send(recipient=RECIPIENT, text=TEXT, image_path=str(img))

        assert result.success is True
        sent = json.loads(resp_mock.calls[0].request.body)
        expected_b64 = base64.b64encode(img.read_bytes()).decode()
        assert sent["base64Jpeg"] == expected_b64


# -----------------------------------------------------------------------
# Tests — erreurs API (success=false)
# -----------------------------------------------------------------------

class TestAPIErrors:

    @resp_mock.activate
    def test_erreur_404_avec_code(self, plugin):
        resp_mock.add(resp_mock.POST, ENDPOINT, json=ERROR_404, status=200)

        with pytest.raises(APIError) as exc_info:
            plugin.send(recipient=RECIPIENT, text=TEXT)

        err = exc_info.value
        assert err.code == 404
        assert "introuvable" in err.error.lower()
        assert err.raw == ERROR_404

    @resp_mock.activate
    def test_erreur_401_sans_code(self, plugin):
        resp_mock.add(resp_mock.POST, ENDPOINT, json=ERROR_401, status=200)

        with pytest.raises(APIError) as exc_info:
            plugin.send(recipient=RECIPIENT, text=TEXT)

        err = exc_info.value
        assert err.code is None
        assert "autoris" in err.error.lower()

    @resp_mock.activate
    def test_erreur_http_500_sans_json(self, plugin):
        resp_mock.add(resp_mock.POST, ENDPOINT, body="Internal Server Error", status=500)

        with pytest.raises(APIError) as exc_info:
            plugin.send(recipient=RECIPIENT, text=TEXT)

        assert exc_info.value.status == 500

    @resp_mock.activate
    def test_erreur_http_401_sans_json(self, plugin):
        resp_mock.add(resp_mock.POST, ENDPOINT, body="Unauthorized", status=401)

        with pytest.raises(APIError) as exc_info:
            plugin.send(recipient=RECIPIENT, text=TEXT)

        assert exc_info.value.status == 401
        assert "token" in exc_info.value.error.lower()


# -----------------------------------------------------------------------
# Tests — erreurs locales
# -----------------------------------------------------------------------

class TestLocalErrors:

    def test_recipient_vide(self, plugin):
        with pytest.raises(ValueError, match="destinataire"):
            plugin.send(recipient="", text=TEXT)

    def test_text_vide(self, plugin):
        with pytest.raises(ValueError, match="texte"):
            plugin.send(recipient=RECIPIENT, text="")

    def test_image_introuvable(self, plugin):
        with pytest.raises(FileNotFoundError):
            plugin.send(recipient=RECIPIENT, text=TEXT, image_path="/inexistant.jpg")

    def test_image_non_jpeg(self, plugin, tmp_path):
        img = tmp_path / "image.png"
        img.write_bytes(b"\x89PNG\r\n")

        with pytest.raises(TypeError, match="JPEG"):
            plugin.send(recipient=RECIPIENT, text=TEXT, image_path=str(img))

    @resp_mock.activate
    def test_timeout(self, plugin):
        resp_mock.add(resp_mock.POST, ENDPOINT, body=requests.Timeout())

        with pytest.raises(requests.Timeout):
            plugin.send(recipient=RECIPIENT, text=TEXT)

    @resp_mock.activate
    def test_connection_error(self, plugin):
        resp_mock.add(resp_mock.POST, ENDPOINT, body=requests.ConnectionError())

        with pytest.raises(requests.ConnectionError):
            plugin.send(recipient=RECIPIENT, text=TEXT)


# -----------------------------------------------------------------------
# Tests — modèle SendMessageResult
# -----------------------------------------------------------------------

class TestSendMessageResult:

    def test_from_dict(self):
        result = SendMessageResult.from_dict(SUCCESS_RESPONSE)
        assert result.success is True
        assert result.phone_number == "+33634058195"
        assert result.type == "SMS"
        assert result.timestamp == 1775425870604

    def test_sent_at_format(self):
        result = SendMessageResult.from_dict(SUCCESS_RESPONSE)
        assert "/" in result.sent_at
        assert ":" in result.sent_at

    def test_str_contient_succes(self):
        result = SendMessageResult.from_dict(SUCCESS_RESPONSE)
        assert "Succès" in str(result)
        assert "+33634058195" in str(result)


# -----------------------------------------------------------------------
# Tests — exception APIError
# -----------------------------------------------------------------------

class TestAPIError:

    def test_str_avec_code(self):
        err = APIError(error="❌ Introuvable", code=404, status=200, timestamp=1775425918484)
        s = str(err)
        assert "Introuvable" in s
        assert "404" in s

    def test_str_sans_code(self):
        err = APIError(error="❌ Non autorisé", status=401, timestamp=1775425983324)
        assert err.code is None
        assert "Non autorisé" in str(err)

    def test_sent_at(self):
        err = APIError(error="test", timestamp=1775425870604)
        assert "/" in err.sent_at
