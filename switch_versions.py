import requests
import backend

def get_switch_versions():
    api_response = backend.get_api('api.json')
    headers = api_response[1]

    session = requests.Session()
    session.headers.update(headers)

    switch_versions = session.get(api_response[0], api_response[1])