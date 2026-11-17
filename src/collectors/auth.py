"""Session seeding for validation targets that redirect anonymous requests to a login page.

Each function logs in from inside the Compose network (service names resolve there) and returns a Cookie
header value for ZAP to send on every request. Credentials are the public defaults of the training apps
(documented by each project), used only on the project-internal network.
"""
import re

import requests

TIMEOUT = 30


def _cookies(resp: requests.Response, names: tuple[str, ...]) -> str:
    jar = resp.cookies
    return "; ".join(f"{n}={jar[n]}" for n in names if n in jar)


def _header(jar: dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in jar.items())


def dvwa(base: str) -> str:
    s = requests.Session()
    setup = s.get(f"{base}/setup.php", timeout=TIMEOUT)  # create tables once (idempotent via the setup form)
    s.post(f"{base}/setup.php", data={"create_db": "Create / Reset Database",
                                      "user_token": re.search(r"name='user_token' value='([0-9a-f]+)'",
                                                              setup.text).group(1)}, timeout=TIMEOUT)
    page = s.get(f"{base}/login.php", timeout=TIMEOUT)
    token = re.search(r"name='user_token' value='([0-9a-f]+)'", page.text).group(1)
    s.post(f"{base}/login.php", data={"username": "admin", "password": "password", "Login": "Login",
                                      "user_token": token}, timeout=TIMEOUT)
    jar = s.cookies.get_dict()
    jar["security"] = "low"  # DVWA's default cookie is 'impossible'; low = all modules vulnerable
    return _header(jar)


def bwapp(base: str) -> str:
    s = requests.Session()
    s.get(f"{base}/install.php?install=yes", timeout=TIMEOUT)  # creates the bWAPP database (idempotent)
    s.post(f"{base}/login.php", data={"login": "bee", "password": "bug", "security_level": "0",
                                      "form": "submit"}, timeout=TIMEOUT)
    return _header(s.cookies.get_dict())


def webgoat(base: str) -> str:
    s = requests.Session()
    user, pw = "wasrascan", "scan1234"  # WebGoat requires 6-10 character passwords
    s.post(f"{base}/register.mvc", data={"username": user, "password": pw, "matchingPassword": pw,
                                         "agree": "agree"}, timeout=TIMEOUT)
    s.post(f"{base}/login", data={"username": user, "password": pw}, timeout=TIMEOUT)
    return "; ".join(f"{c.name}={c.value}" for c in s.cookies)


SEEDERS = {"http://dvwa:80": dvwa, "http://bwapp:80": bwapp, "http://webgoat:8080/WebGoat": webgoat}


def cookie_for(target_url: str) -> str | None:
    """Return a Cookie header value for targets that need a session, else None."""
    for prefix, fn in SEEDERS.items():
        if target_url.startswith(prefix):
            return fn(prefix)
    return None
