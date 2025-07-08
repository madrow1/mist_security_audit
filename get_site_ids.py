import backend
import requests
import json 

def get_site_ids():
    site_list = []
    api_response = backend.get_api('api.json')
    site_ids = requests.get("{}/sites".format(api_response[0]), headers=api_response[1])
    
    site_ids_list = site_ids.json()
    
    for site in site_ids_list:
        site_list.append(site['id'])

    return site_list

def get_device_ids_per_site():
    dev_dict = {}
    dev_list = []
    dev_id_list = []
    api_response = backend.get_site_api('api.json')
    site_ids = get_site_ids()
    
    for site in site_ids:
        #print("{0}{1}/devices".format(api_response[0], site))
        dev_list = ((requests.get("{0}{1}/devices".format(api_response[0], site), headers=api_response[1])).json())

        for i in dev_list:
            # Appends the cleaned data from the request.get to a new list based on the 'id' tag 
            dev_id_list.append(i['id'])
            # Appends the above to the dev_dict based using the site variable to create a json object 
            dev_dict[site] = dev_id_list

    print(dev_dict)
    return dev_dict


#api_response = backend.get_site_api('api.json')

#upgrade_devices = get_device_ids_per_site()

#for site in upgrade_devices:
#    for device in upgrade_devices[site]:
#        requests.post("{0}{1}/devices/{2}/upgrade".format(api_response[0], site, device), headers=api_response[1]).json()


if __name__ =='__get_site_ids__':
    get_site_ids()