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
    recommendations = {}
    score = 0
    count = 0
    
    for element in data:
        # Extract all values once
        enabled = element['enabled']
        auth_settings = element.get('auth', {})
        auth_type = auth_settings.get('type', '')
        # recomendations are only added when required and are adder per WLAN.
        if auth_type == 'open':
            recommendations[element['ssid']] = {"Auth Type Open" : "Use an encrypted authentication method to improve security"}
        enable_mac_auth = auth_settings.get('enable_mac_auth', False)
        private_wlan = auth_settings.get('private_wlan', False)
        radsec_enabled = element.get('radsec', {}).get('enabled', False)
        mist_nac_enabled = element.get('mist_nac', {}).get('enabled', False)
        if mist_nac_enabled == False:
            recommendations[element['ssid']] = {"Mist NAC" : "Enable NAC for more effective security."}
        isolation_settings = element.get('isolation', False)
        if isolation_settings == False:
            recommendations[element['ssid']] = {"Isolation Settings" : "Enable isolation to prevent clients connected to the same AP from communicating"}
        l2_isolation_settings = element.get('l2_isolation', False)
        if l2_isolation_settings == False:
            recommendations[element['ssid']] = {"Enable L2 isolation" : "Enable L2 isolation to prevent clients in the same subnet from communicating"}

        # Only calculate score for enabled WLANs, score is calculated only against metrics that directly influence security.
        if enabled:
            security_checks = [
                auth_type in ['eap', 'psk', 'eap192', 'psk', 'psk-tkip', 'psk-wpa2-tkip', 'wep'],                                      
                mist_nac_enabled,
                isolation_settings,
                l2_isolation_settings
            ]
            

            count += len(security_checks)
            score += sum(security_checks)
        
        # WLAN data forms the dataframe that is displayed in Streamlit. 
        wlan_data.append({
            'SSID': element['ssid'],
            'Enabled': enabled,
            'Auth Type': auth_type,
            'MAC Auth Enabled': enable_mac_auth,
            'Private WLAN': private_wlan,
            'RADSec Enabled': radsec_enabled,
            'Mist NAC Enabled': mist_nac_enabled,
            'Client Isolation': isolation_settings,
            'L2 Client Isolation': l2_isolation_settings
        })

    # Create DataFrame directly from list of dictionaries
    ssid_inv = pd.DataFrame(wlan_data).set_index('SSID')
        
    final_score = (score / count * 100) // 10

    return ssid_inv, int(final_score), recommendations


if __name__ == "__main__":
    get_wlans()