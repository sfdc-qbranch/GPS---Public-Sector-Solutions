import base64
import hashlib
import hmac
import struct
import time
import json
import requests

def qbrix_services_endpoint():
    return "https://qbrix-runtime-service-8c3413c48d7f.herokuapp.com"

def generate_mfa_code(secret):
    # Convert the secret from base32 to bytes
    secret_bytes = base32_to_bytes(secret)

    # Calculate the number of 30-second periods since the epoch
    timestamp = int(time.time() / 30)
    timestamp_bytes = struct.pack(">Q", timestamp)

    # Compute HMAC-SHA1 of the timestamp using the secret as key
    hmac_result = hmac.new(secret_bytes, timestamp_bytes, hashlib.sha1).digest()

    # Extract a 4-byte dynamic binary code from the HMAC result
    offset = hmac_result[-1] & 0x0F
    dbc = struct.unpack(">L", hmac_result[offset:offset+4])[0] & 0x7FFFFFFF

    # Convert the dynamic binary code to a 6-digit number
    mfa_code = dbc % 1000000

    return "{:06d}".format(mfa_code)

def base32_to_bytes(base32_string):
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    padding = len(base32_string) % 8
    base32_string = base32_string + '=' * padding  # Add padding
    result = []

    for i in range(0, len(base32_string), 8):
        chunk = base32_string[i:i+8]
        acc = 0
        for j, char in enumerate(chunk):
            acc = acc | (alphabet.index(char.upper()) << (35 - 5*j))

        result.extend(struct.pack(">Q", acc)[(8 - (5 * len(chunk) + 3) // 8):])

    return bytes(result)

def get_secure_setting(secure_setting: str = None):

    if not secure_setting:
        return None

    endpoint=qbrix_services_endpoint()
    url = f"{endpoint}/QBrixQLabs?settingId={secure_setting}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad responses (4xx, 5xx)
        json_data = response.json()

        if secure_setting in json_data:
            encoded_value = json_data[secure_setting]
            decoded_value = base64.b64decode(encoded_value).decode("utf-8")
            return decoded_value
        else:
            return None  # No "goat" key in the response

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
    
def get_who_am_i(accesstoken: str):
    endpoint=qbrix_services_endpoint()
    url = f"{endpoint}/NeedleCast/whoami"
    payload = json.dumps({"accessToken": f"{accesstoken}"})
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()

def perform_needle_cast(username: str):
    endpoint=qbrix_services_endpoint()
    url = f"{endpoint}/NeedleCast/authenticate"
    payload = json.dumps({"username": f"{username}"})
    headers = {
    'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()
