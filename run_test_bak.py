from check_admin_accounts import check_admin
from check_auto_firmware_update import check_firmware
from check_org_password_policy import check_password_policy
from validate_switch_templates import validate_switch_templates
import streamlit as st 
import matplotlib.pyplot as plt
from datetime import datetime
import json 
import backend
import requests
from get_ap_version import get_ap_firmware_versions
from get_switch_version import get_switch_firmware_versions 
import pandas as pd 
import os 
import concurrent.futures
import io 

st.set_page_config(layout="wide")


def run_checks_concurrently():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            "admin": executor.submit(check_admin),
            "firmware": executor.submit(check_firmware),
            "password": executor.submit(check_password_policy),
            "switch_templates": executor.submit(validate_switch_templates),
            "ap_firmware": executor.submit(get_ap_firmware_versions),
            "switch_firmware": executor.submit(get_switch_firmware_versions),
        }

        admin_score, failing_admins = futures["admin"].result()
        firmware_score, failing_sites = futures["firmware"].result()
        password_score, recommendations = futures["password"].result()
        switch_template_score, switch_fail_log = futures["switch_templates"].result()
        ap_firmware_versions, ap_firmware_recommendations, access_points = futures["ap_firmware"].result()
        switch_firmware_score, switch_firmware_versions, switches = futures["switch_firmware"].result()

    return admin_score, failing_admins, firmware_score, failing_sites, password_score, recommendations, switch_template_score, switch_fail_log, ap_firmware_versions, ap_firmware_recommendations, access_points, switch_firmware_score, switch_firmware_versions, switches

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


    
def pie_chart():
    admin_score, failing_admins, firmware_score, failing_sites, password_score, recommendations, switch_template_score, switch_fail_log, ap_firmware_versions, ap_firmware_recommendations, access_points, switch_firmware_score, switch_firmware_versions, switches = run_checks_concurrently()
    run_tests = True

    # Create tabs
    tab1, tab2 = st.tabs(["Current Score", "Previous Score"])

    timestamp = datetime.today().strftime('%Y-%m-%d %H-%M-%S')
    colors = ['#2D6A00', '#84B135', '#CCDB2A', '#0095A9','#E6ED95','#245200','#FFFFFF']
    max_value = 50

    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[1]}")



    with tab1:
        col1, col2 = st.columns([1, 1], gap='medium')


        with col1:
            while run_tests:
                log = {}

                labels = [f'Admin accounts', "Auto firmware update", "Password policy", "Switch templates", "AP Security", "Switch Security"]
                scores = [admin_score, firmware_score, password_score, switch_template_score, ap_firmware_versions, switch_firmware_score]

                total_value = admin_score + firmware_score + password_score + switch_template_score + ap_firmware_versions + switch_firmware_score
                missing_val = max_value - total_value

                labels.append("")  
                scores.append(missing_val)


                try:
                    with open('sec_audit_log.log', 'r') as file:
                        log = json.load(file)
                except (FileNotFoundError, json.JSONDecodeError):
                    log = {}

                if timestamp not in log:
                    log[timestamp] = {}

                for i, label in enumerate(labels):
                    match label:
                        case "Admin accounts":
                            log[timestamp][label] = {"score": scores[i], "Accounts": failing_admins}
                        case "Auto firmware update":
                            log[timestamp][label] = {"score": scores[i], "Autofirmware update": failing_sites}
                        case "Password policy":
                            log[timestamp][label] = {"score": scores[i], "Password Policy": recommendations}
                        case "Switch templates":
                            log[timestamp][label] = {"score": scores[i], "Switch Templates": switch_fail_log}
                        case "AP Security":
                            log[timestamp][label] = {"score": scores[i], "AP Firmware": ap_firmware_recommendations}
                        case "Switch Security":
                            log[timestamp][label] = {"score": scores[i], "Switch firmware": switch_firmware_versions}
                        case _:
                            log[timestamp][label] = {"score": scores[i]}

                with open('sec_audit_log.log', 'w') as file:
                    json.dump(log, file, indent=4)

                fig1, ax1 = plt.subplots(figsize=(15, 15))
                wedges, texts, autotexts = ax1.pie(scores, labels=labels, colors=colors,
                                                   autopct=lambda p: f'{p * sum(scores) / 100:.0f}', pctdistance=0.8,
                                                   startangle=90, wedgeprops={'width': 0.4})
                ax1.text(0, 0, f"{total_value}/{max_value}", horizontalalignment='center', verticalalignment='center',
                         fontsize=36, fontweight='bold')
                ax1.axis('equal')

                for text in texts:
                    text.set_fontsize(28)
                    text.set_color('black')
                    text.set_fontweight('bold')

                for autotext in autotexts:
                    autotext.set_fontsize(36)
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')

                col1.title("Mist org security audit")
                st.pyplot(fig1)  

                with col2:
                    col2.title("Current issues")
                    st.subheader(f"Password security: {password_score}/10")
                    st.text(json_to_bullet_points(recommendations))
                    if st.button("Apply recommended password fixes", key=f'password_recommended_solution{timestamp}'):
                        update_password(api_response=backend.get_api('api.json'))
                    st.subheader(f"Auto firmware Update: {firmware_score}/10")
                    st.text(json_to_bullet_points(failing_sites))
                    if st.button("Apply recommended autoupgrade firmware fixes", key=f'firmware_recommended_solution{timestamp}'):
                        update_password(api_response=backend.get_api('api.json'))
                    st.subheader(f"Admin account security: {admin_score}/10")
                    st.text(json_to_bullet_points(failing_admins))
                    st.subheader(f"Switch template recommendations: {switch_template_score}/10")
                    st.text(json_to_bullet_points(switch_fail_log))
                    if st.button("Apply recommended switch template fixes", key=f'switch_template_recommended_solution{timestamp}'):
                        update_password(api_response=backend.get_api('api.json'))    
                    st.subheader(f"AP security: {ap_firmware_versions}/10")
                    st.text(json_to_bullet_points(ap_firmware_recommendations))
                    st.subheader(f"Switch security: {switch_firmware_score}/10")
                    st.text(json_to_bullet_points(switch_firmware_versions))



                run_tests = False  

            if st.button("Re-run test", key=f"rerun_button{timestamp}"):
                run_tests = True


    with tab2:
            col1, col2 = st.columns([1,1], gap='medium')
            with col1:
                with open('sec_audit_log.log', 'r') as p_log:
                    data = json.load(p_log)
                    keys = list(data.keys())

                    latest_timestamp = keys[-1]
                    latest_data = data[latest_timestamp]

                    p_scores = []
                    p_labels = ['Admin accounts', "Auto firmware update", "Password policy", "Switch templates", "AP Security", "Switch Security", ""]

                    for label, details in latest_data.items():
                        score = details.get('score')
                        if score is not None:
                            p_scores.append(score)

                    p_total_value = sum(p_scores) - p_scores[-1]

                    fig2, ax2 = plt.subplots(figsize=(15, 15))
                    wedges, texts, autotexts = ax2.pie(p_scores, labels=p_labels, colors=colors,
                                                    autopct=lambda p: f'{p * sum(p_scores) / 100:.0f}', pctdistance=0.8,
                                                    startangle=90, wedgeprops={'linewidth':2, 'width': 0.4})
                    ax2.text(0, 0, f"{p_total_value}/{max_value}", horizontalalignment='center', verticalalignment='center',
                            fontsize=36, fontweight='bold')
                    ax2.axis('equal')

                    for text in texts:
                        text.set_fontsize(28)
                        text.set_color('black')
                        text.set_fontweight('bold')

                    for autotext in autotexts:
                        autotext.set_fontsize(36)
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')

                    col1.title("Mist org security audit")
                    st.pyplot(fig2)  

            with col2:
                st.title("Most recent issues")
                st.subheader("Password security")
                st.text(json_to_bullet_points(latest_data['Password policy']))
                st.subheader("Auto Firmware Update")
                st.text(json_to_bullet_points(latest_data['Auto firmware update']))
                st.subheader("Admin account security")
                st.text(json_to_bullet_points(latest_data['Admin accounts']))
                st.subheader("Switch template security")
                st.text(json_to_bullet_points(latest_data['Switch templates']))
                st.subheader("AP security")
                st.text(json_to_bullet_points(latest_data['AP Security']))
                st.subheader("Switch security")
                st.text(json_to_bullet_points(latest_data['Switch Security']))

def switch_inventory():
    switch_firmware_score, switch_firmware_versions, switches = get_switch_firmware_versions()

    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[2]}")

    switch_firmware_dict = {
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

    firmware_styles = {
        '0.12.27139': 'background-color: yellow',
        '0.14.29633': 'background-color: white',
        '0.10.24626': 'background-color: orange',
        '0.8.21804': 'background-color: red'
    }

    def highlight_row(row):
        required_columns = ['Root password', 'DHCP snooping']

        styles = [''] * len(row)

        if all(pd.notna(row[required_columns]) & (row[required_columns] != '')):
            for col in required_columns:
                col_index = row.index.get_loc(col)
                styles[col_index] = 'background-color: red'

        switch_name = row['Model']  
        firmware_version = switch_firmware_dict.get(switch_name[:8], None)

        if firmware_version:
            firmware_cell_value = row['Firmware']

            if firmware_version != firmware_cell_value:
                style = 'background-color: red' 
                if 'Firmware' in row.index:
                    firmware_index = row.index.get_loc('Firmware')
                    styles[firmware_index] = style
                else:
                    style = 'background-color: white' 
                    if 'Firmware' in row.index:
                        firmware_index = row.index.get_loc('Firmware')
                        styles[firmware_index] = style 

        return styles
        
    switch_inv = pd.DataFrame(switches).T
    switch_inv.columns = ['Model', 'Name', 'Firmware', 'Site_ID', 'Device ID', 'Root password', 'DHCP snooping']
    styled_switch_inv = switch_inv.style.apply(highlight_row, axis=1)
    
    df = st.dataframe(styled_switch_inv)

    csv = convert_for_download(switch_inv)

    st.download_button(
        label="Download Switch Inventory",
        data=csv,
        file_name='switch_inventory.csv'
    )

def ap_inventory():
    ap_firmware_versions, ap_firmware_recommendations, access_points = get_ap_firmware_versions()

    ap_firmware_dict = {
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
        "AP41": "0.12.27139",
        "AP61": "0.12.27139",
        "AP21": "0.8.21804",
        "BT11": "0.8.21804"
    }

    firmware_styles = {
        '0.12.27139': 'background-color: yellow',
        '0.14.29633': 'background-color: white',
        '0.10.24626': 'background-color: orange',
        '0.8.21804': 'background-color: red'
    }
    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[3]}")

    def highlight_row(row):
        styles = ['']*len(row)
        ap_name = row['Model']  

        firmware_version = ap_firmware_dict.get(ap_name, None)

        if firmware_version:
            style = firmware_styles.get(firmware_version, 'background-color: gray') 
            firmware_index = row.index.get_loc('Firmware')
            styles[firmware_index] = style

        return styles

    ap_inv = pd.DataFrame(access_points).T
    ap_inv.columns = ['Model', 'Name', 'Firmware', 'Site_ID']

    styled_ap_inv = ap_inv.style.apply(highlight_row, axis=1)

    st.dataframe(styled_ap_inv)

    csv = convert_for_download(ap_inv)

    st.download_button(
        label="Download AP Inventory",
        data=csv,
        file_name='ap_inventory.csv'
    )

#def mist_edge_inventory():
#    with st.sidebar:
#        st.markdown(f"# {list(page_names_to_funcs.keys())[1]}")
#
#    ap_inv = pd.DataFrame(access_points).T
#    ap_inv.columns = ['Model', 'Name', 'Firmware', 'Site_ID']
#    df = st.data_editor(ap_inv)

#def site_admins():
#    admin_score, failing_admins = check_admin()
#    with st.sidebar:
#        st.markdown(f"# {list(page_names_to_funcs.keys())[1]}")

def raw_logs():
    count = 0
    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[4]}")

    try:
        with open('sec_audit_log.log', 'r') as logs:
            log_data = json.load(logs)

            for timestamp, log_entries in log_data.items():
                if count >= 100:  
                    break
                st.subheader(f"Timestamp: {timestamp}")
                
                for entry, details in log_entries.items():
                    log_entry = (f"{entry}: {details}")
                    st.markdown(
                        f'<div style="background-color:#f0f0f0; padding: 10px; margin-bottom: 10px; border-radius: 5px;">{log_entry}</div>',
                        unsafe_allow_html=True
                    )
                    count += 1

    except FileNotFoundError:
        st.error("Log file 'sec_audit_log.log' not found.")
    except json.JSONDecodeError:
        st.error("Failed to decode the JSON log file. Please check the file format.")

    with open('sec_audit_log.log', 'r') as log_file:
        st.download_button("Download log file", data=log_file, file_name='sec_audit_log.log')

def org_settings():
    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[0]}")

    st.title("Enter org details below")
    org_id = st.text_input("Org ID")
    token = st.text_input("API Token")
    url = st.text_input("Site URL")

    if org_id and token and url:
        data = {
            "api": {
                "org_id": org_id,
                "token": token,
                "mist_url": url
            }
        }

        file_path = "api.json"

        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)
        
        st.success(f"JSON file created and saved as {file_path}")        
    else:
        st.error("Please fill in all the fields")

    if url:
        st.rerun()


def update_password(api_response):
    raw_data = json.dumps({"password_policy": {"enabled": True,
                                "min_length": 16,
                                "requires_special_char": True,
                                "requires_two_factor_auth": True}})
    
    requests.put("{}/setting".format(api_response[0]), data=raw_data, headers=api_response[1])

def update_firmware(api_response):
    return 0

def switch_template_recomendations(api_response):
    return 0

def convert_for_download(df):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return csv_buffer.getvalue()

if not os.path.exists('api.json'):
    page_names_to_funcs = {
        "Org settings": org_settings,
    }
else:
    page_names_to_funcs = {
        "Org settings": org_settings,
        "Pie Chart": pie_chart,
        "Switch inventory": switch_inventory,
        "AP inventory": ap_inventory,
        "Raw log files": raw_logs
    }


demo_name = st.sidebar.selectbox("Choose demo", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()