import requests
import backend 
import json 

def validate_switch_templates():
    result = {}
    fail_log = {} 
    score = 0
    count = 0
    api_response = backend.get_api('api.json')
    api_url, headers = api_response[0], api_response[1]

    response = requests.get(f"{api_url}/networktemplates", headers=headers)
    data = response.json()

    def check_condition(obj, value, site_id, template_name):
        if value is None or len(value) == 0:
            log_failure(template_name, obj, "Value is None or empty")
            return "fail"  
        else:
            match obj:
                case "ntp_servers" | "dns_servers":
                    if len(value) == 1:
                        return "success"
                    else:
                        log_failure(template_name, obj, "Length of value is not 1")
                        return "fail"
                case "remote_syslog" | "dhcp_snooping" | "mist_nac":
                    if True:
                        return "success"
                    else:
                        log_failure(template_name, obj, "Condition failed for remote_syslog, dhcp_snooping, or mist_nac")
                        return "fail"
                case "radius_config":
                    if isinstance(value, dict) and "auth_servers" in value:
                        return "success" 
                    else:
                        log_failure(template_name, obj, "Missing 'auth_servers' in radius_config")
                        return "fail"

    def log_failure(site_id, obj, reason):
        if site_id not in fail_log:
            fail_log[template_name] = []
        fail_log[template_name].append({
            "Issue": obj,
            "Reason": reason,
        })

    for site_object in data:
        site_id = site_object["id"]
        template_name = site_object['name']

        try:
            single_switch_response = requests.get(f"{api_url}/networktemplates/{site_id}", headers=headers)
            single_switch_data = single_switch_response.json()

            if site_id not in result:
                result[site_id] = []

            for obj, value in single_switch_data.items():
                if value is None or obj not in ["ntp_servers","dns_servers","remote_syslog","dhcp_snooping","mist_nac","radius_config"]:
                    continue  
                else:
                    result[site_id].append(f"{obj}, {check_condition(obj, value, site_id, template_name)}")  

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for site {site_id}: {e}")
        except ValueError as e:
            print(f"ValueError: {e}")
        except TypeError as e:
            print(f"TypeError encountered for site {site_id}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred for site {site_id}: {e}")

    for field in result:
        for results in result[field]:
            if "success" in results:
                score += 1
                count += 1 
            else:
                count += 1

    final_score = (score / count * 100) // 10


    return int(final_score),fail_log

if __name__ == "__main__":
    validate_switch_templates()


    