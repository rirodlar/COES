"""Small helper for authenticating against the DSpace REST API from scripts.

Reads credentials from environment variables so they never live in source:
    DSPACE_REST_URL       e.g. http://127.0.0.1:8080/server (default)
    DSPACE_ADMIN_EMAIL
    DSPACE_ADMIN_PASSWORD
"""
import os
import urllib.request

BASE_SERVER = os.environ.get("DSPACE_REST_URL", "http://127.0.0.1:8080/server")


def _get_csrf():
    req = urllib.request.Request(f"{BASE_SERVER}/api/authn/status")
    with urllib.request.urlopen(req) as resp:
        for h, v in resp.getheaders():
            if h.upper() == "DSPACE-XSRF-TOKEN":
                return v
    return None


def get_auth_headers():
    """Logs in using DSPACE_ADMIN_EMAIL / DSPACE_ADMIN_PASSWORD and returns
    the headers dict needed for authenticated requests."""
    email = os.environ["DSPACE_ADMIN_EMAIL"]
    password = os.environ["DSPACE_ADMIN_PASSWORD"]

    csrf = _get_csrf()
    data = f"user={email}&password={password}".encode()
    req = urllib.request.Request(
        f"{BASE_SERVER}/api/authn/login", data=data, method="POST",
        headers={
            "X-XSRF-TOKEN": csrf,
            "Cookie": f"DSPACE-XSRF-COOKIE={csrf}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req) as resp:
        token = None
        new_csrf = csrf
        for h, v in resp.getheaders():
            if h.upper() == "AUTHORIZATION":
                token = v
            if h.upper() == "DSPACE-XSRF-TOKEN":
                new_csrf = v

    return {
        "Authorization": token,
        "X-XSRF-TOKEN": new_csrf,
        "Cookie": f"DSPACE-XSRF-COOKIE={new_csrf}",
    }
