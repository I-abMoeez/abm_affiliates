import os
import requests


def get_country_from_ip(ip: str) -> tuple[str | None, str | None]:
    """Return (country_code, country_name) from an IP.

    Uses a free provider. If it fails, returns (None, None).
    """

    if not ip:
        return None, None

    provider = os.getenv("IP_GEO_PROVIDER", "ipapi")

    try:
        if provider == "ipapi":
            # ip-api.com (free tier)
            # https://ip-api.com/docs/api:json
            url = f"http://ip-api.com/json/{ip}?fields=countryCode,country"
            timeout = float(os.getenv("IP_GEO_TIMEOUT", "3"))
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            data = r.json() if hasattr(r, "json") else {}

            # ip-api returns {status:"success"...} or {status:"fail"...}
            if str(data.get("status")) != "success":
                return None, None

            return data.get("countryCode"), data.get("country")

        # Unknown provider
        return None, None
    except Exception:
        return None, None

