import requests
import backend 
import json 

def get_ap_firmware_versions():
    score = 0
    count = 0
    access_points = {}
    version_dict = {}
    recomendation = {}
    sites = backend.get_sites("api.json")
    api_response = backend.get_site_api("api.json")
    org_response = backend.get_api("api.json")
    headers = api_response[1]

    #versions = requests.get("{}/devices/versions".format(org_response[0]), headers=headers)

    #version_data = versions.json()

    for key in sites:
        site_settings = requests.get("{0}{1}/stats/devices".format(api_response[0], sites[key]), headers=headers)
        data = site_settings.json()

        for access_point in data:
            access_points[access_point['serial']] = [access_point['model'], access_point['name'], access_point['version'], access_point['site_id']]


    version_dict = {
        "AP45": "0.12.27139",
        "AP34": "0.12.27139",
        "AP24": "0.14.29633",
        "AP64": "0.14.29633",
        "AP43": "0.10.24626",
        "AP63": "0.12.27139",
        "AP43-FIPS": "0.10.24626",
        "AP12": "0.12.27139",
        "AP32": "0.12.27139",
        "AP33": "0.12.27139",
        "AP41": "0.12.27452",
        "AP61": "0.12.27139",
        "AP21": "0.8.21804",
        "BT11": "0.8.21804"
    }

    for serial, ap_data in access_points.items():
        model = ap_data[0]
        current_version = ap_data[2]
        
        # Check if the model exists in version_dict and if the current version matches the recommended one
        recommended_version = version_dict.get(model)
        if current_version == recommended_version:
            score += 1
        else:
            recomendation[serial] = f"Firmware out of date, recommended firmware is {recommended_version}"
        count += 1

    final_score = (score / count * 100) // 10

    return int(final_score), recomendation, access_points
                

if __name__ == "__main__":
    get_ap_firmware_versions()