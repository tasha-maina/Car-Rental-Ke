"""Minimal Safaricom Daraja STK-push client (stdlib only)."""
import base64
import json
import re
import urllib.error
import urllib.request
from datetime import datetime

from django.conf import settings


class MpesaError(Exception):
    pass


def _base():
    return "https://api.safaricom.co.ke" if settings.MPESA_ENV == "production" else "https://sandbox.safaricom.co.ke"


def _call(req):
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("errorMessage", e.reason)
        except Exception:
            msg = e.reason
        raise MpesaError(msg)
    except Exception as e:
        raise MpesaError(str(e))


def _token():
    cred = base64.b64encode(f"{settings.MPESA_CONSUMER_KEY}:{settings.MPESA_CONSUMER_SECRET}".encode()).decode()
    req = urllib.request.Request(f"{_base()}/oauth/v1/generate?grant_type=client_credentials",
                                 headers={"Authorization": f"Basic {cred}"})
    return _call(req)["access_token"]


def normalize_phone(phone):
    p = re.sub(r"\D", "", phone)
    if p.startswith("0"):
        p = "254" + p[1:]
    return p


def stk_push(phone, amount, ref):
    """Returns CheckoutRequestID."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{ts}".encode()).decode()
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE, "Password": password, "Timestamp": ts,
        "TransactionType": settings.MPESA_TRANSACTION_TYPE, "Amount": int(amount),
        "PartyA": normalize_phone(phone), "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": normalize_phone(phone), "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": ref, "TransactionDesc": f"Car rental {ref}",
    }
    req = urllib.request.Request(f"{_base()}/mpesa/stkpush/v1/processrequest",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"})
    data = _call(req)
    if data.get("ResponseCode") != "0":
        raise MpesaError(data.get("ResponseDescription", "request rejected"))
    return data["CheckoutRequestID"]
