import backend
import requests

def main():
    api_response = backend.get_api('api.json')
    print("Expected response is 200")
    print(requests.get(api_response[0], headers=api_response[1]))
    
if __name__ =='__main__':
    main()