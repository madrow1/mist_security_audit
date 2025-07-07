import requests
import backend 
import json 
import re 

def get_switch_firmware_versions():
    score = 0
    count = 0
    switches = {}
    recomendation = {}
    sites = backend.get_sites("api.json")
    api_response = backend.get_site_api("api.json")
    org_response = backend.get_api("api.json")
    headers = api_response[1]
    params = {'type': 'switch'}
    dev_data = {}
    #versions = requests.get("{}/devices/versions".format(org_response[0]), headers=headers)

    #version_data = versions.json()

    for key in sites:
        site_settings = requests.get("{0}{1}/stats/devices".format(api_response[0], sites[key]), headers=headers, params=params)
        devices = requests.get("{0}{1}/devices?type=all".format(api_response[0], sites[key]), headers=headers, params=params)

        data = site_settings.json()
        device_data = devices.json()

        for switch in data:
            for device in device_data:
                switches[switch['serial']] = [switch['model'], switch['name'], switch['version'], switch['site_id'], device['id']]

        for device in device_data:
            data_types = ['ntp_servers', 'dns_servers', 'dhcp_snooping']
            s_device_data = requests.get("{0}{1}/devices/{2}".format(api_response[0], sites[key], device['id']), headers=headers, params=params)
            dev_data = s_device_data.json()
            #print(dev_data)
            
            for dev in dev_data:
                match dev:
                    case 'switch_mgmt':
                       switches[dev_data['serial']].append(dev_data[dev])
                       recomendation[dev_data['serial']] = ["Password should be left blank"]
                       count += 1
                    #case 'ntp_servers':            
                       #switches[dev_data['serial']].append(dev_data[dev])
                    #case 'dns_servers':
                       #switches[dev_data['serial']].append(dev_data[dev])
                    #case 'dhcp_snooping':
                       #switches[dev_data['serial']].append(dev_data[dev])
                    #case 'radius_config':
                    #    switches[dev_data['serial']].append(dev_data[dev])
                    



    platforms = {
        "EX2200": "12.3R12",
        "EX2200-C": "12.3R12",
        "EX2300": "23.4R2",
        "EX2300-C": "23.4R2",
        "EX2300-MP": "23.4R2",
        "EX3200": "12.3R12",
        "EX3300": "12.3R12",
        "EX3400": "23.4R2",
        "EX4100": "23.4R2-S4",
        "EX4100-F": "23.4R2-S4",
        "EX4100-H": "24.4R1",
        "EX4200": "12.3R12 / 15.1R7",
        "EX4300": "21.4R3",
        "EX4300-MP": "23.4R2",
        "EX4400": "23.4R2",
        "EX4400-24X": "23.4R2",
        "EX4500": "12.3R12 / 15.1R7",
        "EX4550": "12.3R12 / 15.1R7",
        "EX4600": "21.4R3",
        "EX4650": "23.4R2",
        "EX6200": "12.3R12 / 15.1R7",
        "EX8200": "12.3R12 / 15.1R7",
        "EX8200-VC (XRE200)": "12.3R12 / 15.1R7",
        "EX9200": "23.4R2",
        "EX9251": "21.4R3",
        "EX9253": "21.4R3"
    }


    for serial, switch_data in switches.items():
        model = switch_data[0]
        current_version = switch_data[2]
        
        # Check if the model exists in version_dict and if the current version matches the recommended one
        recommended_version = platforms.get(model[:8].upper())
        if current_version[:6] == recommended_version:
            score += 1
        else:
            recomendation[serial] = (f"Firmware out of date, recommended firmware is {recommended_version}")
        count += 1



    final_score = (score / count * 100) // 10


    return int(final_score), recomendation, switches

if __name__ == "__main__":
    get_switch_firmware_versions()