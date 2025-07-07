import json 
import backend
import requests 
import pandas as pd 


def get_wlans():
    api_response = backend.get_api('api.json')
    response = requests.get(f"{api_response[0]}/wlans", headers=api_response[1])
    data = response.json()

    # Process data more efficiently
    wlan_data = []
    score = 0
    count = 0
    
    for element in data:
        # Extract all values once
        enabled = element['enabled']
        auth_settings = element.get('auth', {})
        auth_type = auth_settings.get('type', '')
        enable_mac_auth = auth_settings.get('enable_mac_auth', False)
        private_wlan = auth_settings.get('private_wlan', False)
        radsec_enabled = element.get('radsec', {}).get('enabled', False)
        mist_nac_enabled = element.get('mist_nac', {}).get('enabled', False)
        
        # Only calculate score for enabled WLANs
        if enabled:
            security_checks = [
                auth_type in ['eap', 'psk', 'eap192', 'psk', 'psk-tkip', 'psk-wpa2-tkip', 'wep'],  
                enable_mac_auth,              
                private_wlan,                
                radsec_enabled,               
                mist_nac_enabled              
            ]
            
            count += len(security_checks)
            score += sum(security_checks)
        
        wlan_data.append({
            'SSID': element['ssid'],
            'Enabled': enabled,
            'Auth Type': auth_type,
            'MAC Auth Enabled': enable_mac_auth,
            'Private WLAN': private_wlan,
            'RADSec Enabled': radsec_enabled,
            'Mist NAC Enabled': mist_nac_enabled
        })

    # Create DataFrame directly from list of dictionaries
    ssid_inv = pd.DataFrame(wlan_data).set_index('SSID')
        
    final_score = (score / count * 100) // 10

    return ssid_inv, int(final_score) 

if __name__ == "__main__":
    get_wlans()