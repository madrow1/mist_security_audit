import json 
import requests
import argparse

def get_api(file):
    f = open(file)
    configs = json.load(f)

    api_url = '{0}orgs/{1}'.format(configs['api']['mist_url'],configs['api']['org_id'])
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Token {}'.format(configs['api']['token'])}
    
    return api_url,headers

def get_site_api(file):
    f = open(file)
    configs = json.load(f)

    api_url = '{0}sites/'.format(configs['api']['mist_url'])
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Token {}'.format(configs['api']['token'])}
    
    return api_url,headers

def get_sites(file):
    site_ids = {}
    api_response = get_api('api.json')
    response = requests.get("{}/sites".format(api_response[0]), headers=api_response[1])   
    data = response.json()

    keys = ["name", "id"]

    for site in data:
        for field in site:
            match field:
                case "name":
                    site_name = site[field]
                case "id":
                    site_id = site[field]
        site_ids[site_name] = site_id

    return site_ids

def read_json_list(file):
    f = open(file)
    json_file = json.load(f)
    return json_file

def create_site(config):
    #"config" is passed from the .py file to the API, and is the file containing site configuration data.
    apos_site = {}
    apos_site['name'] = config['name']
    apos_site['timezone'] = config['timezone']
    apos_site['country_code'] = config['country_code']
    apos_site['latlng'] = {'lat': config['lat'], 'lng': config['lng']}
    apos_site['address'] = config['address']

    # 
    data_post = json.dumps(apos_site)

    api_response = get_api('api.json')

    response = requests.post(api_response[0], data=data_post, headers=api_response[1])
    new_site = json.loads(response.content.decode('utf-8'))

    if response.status_code == '200':
        print("Site {} created succesfully".format(apos_site['name']))
    else:
        print("Site {} creation failed".format(apos_site['name']))

def json_to_bullet_points(json_data):
    bullet_points = ""
    
    def process_item(key, value, indent=0):
        nonlocal bullet_points
        indent_str = "  " * indent  
        
        if isinstance(value, dict): 
            if key:  
                bullet_points += f"{indent_str}• {key}: \n"
            for sub_key, sub_value in value.items():
                process_item(sub_key, sub_value, indent + 1)
        elif isinstance(value, list):  
            bullet_points += f"{indent_str}• {key}: \n" if key else ""  
            for item in value:
                if isinstance(item, dict): 
                    process_item('', item, indent + 1)
                else:
                    bullet_points += f"{indent_str}  - {item}\n"
        else:  
            bullet_points += f"{indent_str}• {key}: {value}\n" if key else ""
    
    for key, value in json_data.items():
        process_item(key, value)
    
    return bullet_points