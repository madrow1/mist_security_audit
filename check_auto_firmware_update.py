import requests
import backend 
import json 

def check_firmware():
    score = 0 
    site_statue = {}
    failing_sites = {"Failing sites, auto-firmware upgrade should be enabled for the below sites" : []}
    # Note that if no settings have been changed at the org level then Mist does not populate this response.
    #response = requests.get("{}/sites".format(api_response[0]), headers=api_response[1])
    sites = backend.get_sites("api.json")

    backend_call = backend.get_site_api("api.json")
    record = {}
    count = 0
    score = 0 

    for key in sites:
        site_settings = requests.get("{0}{1}/setting".format(backend_call[0], sites[key]), headers=backend_call[1])
        data = site_settings.json()
        auto_update_status = json.dumps(data['auto_upgrade']['enabled'])
        record[key] = auto_update_status
        


    for entry in record:
        match record[entry]:
            case "true":
                score +=1
                count +=1
            case "false":
                count += 1
                failing_sites["Failing sites, auto-firmware upgrade should be enabled for the below sites"].append(entry)

    final_score = (score / count * 100) // 10

    #print(int(final_score))
    #print(failing_sites)

    return int(final_score), failing_sites


if __name__ == "__main__":
    check_firmware()