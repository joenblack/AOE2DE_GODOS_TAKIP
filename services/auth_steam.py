import urllib.parse
import requests
import re

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

class SteamAuth:
    def __init__(self, realm: str, return_to: str):
        self.realm = realm
        self.return_to = return_to

    def get_login_url(self):
        """
        Generates the Steam OpenID login URL.
        """
        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": self.return_to,
            "openid.realm": self.realm,
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
        return f"{STEAM_OPENID_URL}?{urllib.parse.urlencode(params)}"

    def validate(self, params: dict):
        """
        Validates the response from Steam.
        Returns the SteamID (64-bit integer string) if valid, or None.
        """
        # We need to validate the params with Steam
        # Copy params to avoid mutation
        validation_params = params.copy()
        
        # Switch mode to check_authentication
        validation_params['openid.mode'] = 'check_authentication'
        
        try:
            response = requests.post(STEAM_OPENID_URL, data=validation_params)
            if "is_valid:true" in response.text:
                # Extract Steam ID from claimed_id
                # Format: https://steamcommunity.com/openid/id/<steamid>
                claimed_id = params.get("openid.claimed_id", "")
                match = re.search(r"https://steamcommunity.com/openid/id/(\d+)", claimed_id)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"Steam validation error: {e}")
            
        return None
