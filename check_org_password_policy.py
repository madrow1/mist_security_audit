import requests
import backend 
import json 

def check_password_policy():
    score = 0 
    recomendations = {"Password Policy Recommendation": "", "Minimum Length Recommendation": "", "Special Char Recommendation": "", "2FA Recommendation": ""}
    api_response = backend.get_api('api.json')
    # Note that if no settings have been changed at the org level then Mist does not populate this response.
    response = requests.get("{}/setting".format(api_response[0]), headers=api_response[1])
    data = response.json()
    if 'password_policy' not in data: 
        print("Org settings may not have been edited at all, the API is not populated before site configuration")
        exit()

    match data['password_policy']['enabled']:
        case True:
            score += 2
            recomendations.update({"Password Policy Recommendation": "No recommendation, policy set"})
        case False:
            recomendations.update({"Password Policy Recommendation": "Enable password policies"})
            next

    if data['password_policy']['enabled'] == True:
        match data['password_policy']['min_length']:
            case x if x <= 8:
                recomendations.update({"Minimum Length Recommendation": "Increase length to greater than 8 characters"})
                next
            case x if x > 8 and x <= 12:
                recomendations.update({"Minimum Length Recommendation": "Consider increasing length to greater than 12 characters"})
                score += 2
            case x if x > 12:
                recomendations.update({"Minimum Length Recommendation": "No recommendation"})
                score += 4

        match data['password_policy']['requires_special_char']:
            case True:
                score += 2 
                recomendations.update({"Special Char Recommendation": "No recommendation, policy set"})
            case False:
                recomendations.update({"Special Char Recommendation": "Enable special characters"})
                next

        match data['password_policy']['requires_two_factor_auth']:
            case True:
                score += 2
                recomendations.update({"2FA Recommendation": "No recommendation, Policy set"})
            case False:
                recomendations.update({"2FA Recommendation": "Enable 2FA"})
                next
        
        #print(json.dumps(recomendations, indent=2))

        raw_data = json.dumps({"password_policy": {"enabled": True,
                                        "min_length": 16,
                                        "requires_special_char": True,
                                        "requires_two_factor_auth": True}})
        
        #secure_org = input("Would you like this script to automatically update your org settings for maximum security? y/n")

    else:
        recomendations.update({"Password Policy": "Password policy is disabled"})
        score == 0 

    return score, recomendations, 

def update_password(api_response):
    raw_data = json.dumps({"password_policy": {"enabled": True,
                                "min_length": 16,
                                "requires_special_char": True,
                                "requires_two_factor_auth": True}})
    
    requests.put("{}/setting".format(api_response[0]), data=raw_data, headers=api_response[1])


if __name__ == "__main__":
    check_password_policy()

    