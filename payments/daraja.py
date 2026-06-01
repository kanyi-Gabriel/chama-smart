import requests
import base64
from datetime import datetime
from django.conf import settings


def get_access_token():
    """
    Every Daraja API call needs a fresh access token.
    This function gets one using your Consumer Key and Secret.
    Think of it like logging in before making a request.
    """
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET

    if settings.MPESA_ENVIRONMENT == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    else:
        url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'

    response = requests.get(url, auth=(consumer_key, consumer_secret))
    token = response.json().get('access_token')
    return token


def generate_password():
    """
    Daraja requires a password made from:
    Shortcode + Passkey + Current Timestamp
    All joined together and base64 encoded.
    """
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

    raw = f"{shortcode}{passkey}{timestamp}"
    encoded = base64.b64encode(raw.encode()).decode()
    return encoded, timestamp


def stk_push(phone_number, amount, account_reference, description):
    """
    Triggers the M-Pesa payment prompt on a member's phone.

    phone_number: format 2547XXXXXXXX (254 + number without leading 0)
    amount: integer, e.g. 500
    account_reference: e.g. "CHAMA001" 
    description: e.g. "Monthly contribution"
    """
    access_token = get_access_token()
    password, timestamp = generate_password()

    if settings.MPESA_ENVIRONMENT == 'sandbox':
        url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    else:
        url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'BusinessShortCode': settings.MPESA_SHORTCODE,
        'Password': password,
        'Timestamp': timestamp,
        'TransactionType': 'CustomerPayBillOnline',
        'Amount': int(amount),
        'PartyA': phone_number,
        'PartyB': settings.MPESA_SHORTCODE,
        'PhoneNumber': phone_number,
        'CallBackURL': settings.MPESA_CALLBACK_URL,
        'AccountReference': account_reference,
        'TransactionDesc': description
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()