from check_admin_accounts import check_admin
from check_auto_firmware_update import check_firmware
from check_org_password_policy import check_password_policy
from validate_switch_templates import validate_switch_templates
from get_site_ids import get_site_ids, get_device_ids_per_site
import streamlit as st 
import matplotlib.pyplot as plt
from datetime import datetime
import json 
import backend
import requests
from get_ap_version import get_ap_firmware_versions
from get_switch_version import get_switch_firmware_versions 
from get_wlan_sec_settings import get_wlans
import pandas as pd 
import os 
import concurrent.futures
import io 
import numpy as np 


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
            "wlans": executor.submit(get_wlans),
        }

        admin_score, failing_admins = futures["admin"].result()
        firmware_score, failing_sites = futures["firmware"].result()
        password_score, recommendations = futures["password"].result()
        switch_template_score, switch_fail_log = futures["switch_templates"].result()
        ap_firmware_score, ap_firmware_recommendations, access_points = futures["ap_firmware"].result()
        switch_firmware_score, switch_firmware_versions, switches = futures["switch_firmware"].result()
        wlans_table, wlan_score = futures["wlans"].result()

    return admin_score, failing_admins, firmware_score, failing_sites, password_score, recommendations, switch_template_score, switch_fail_log, ap_firmware_score, ap_firmware_recommendations, access_points, switch_firmware_score, switch_firmware_versions, switches, wlans_table, wlan_score

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
    admin_score, failing_admins, firmware_score, failing_sites, password_score, recommendations, switch_template_score, switch_fail_log, ap_firmware_score, ap_firmware_recommendations, access_points, switch_firmware_score, switch_firmware_versions, switches, wlans_table, wlan_score = run_checks_concurrently()
    run_tests = True

    # Create tabs
    tab1, tab2 = st.tabs(["Current Score", "Previous Score"])

    timestamp = datetime.today().strftime('%Y-%m-%d %H-%M-%S')
    # Assign colors to sections of the pie chart. A new color needs to be added each time a new object is added, otherwise the section will be white.
    # This could be automated, however for consistency (and to keep the colours to Juniper official) I have kept it manual for now;
    colors = ['#2D6A00', '#84B135', '#CCDB2A', '#0095A9','#E6ED95','#245200', '#E87200','#FFFFFF']


    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[1]}")
        st.markdown("   - The pie chart is generated based off of API calls made to the Mist organisation")
        st.markdown("   - The buttons to apply fixes on this page will apply to all devices in an organisation, so care should be taken if you do not want to upgrade all devices")
        st.markdown("   - All scores can be viewed under the Raw Logs Tab")


    with tab1:
        col1, col2 = st.columns([1, 1], gap='medium')

        with col1:
            while run_tests:
                log = {}

                # Original labels and scores
                all_labels = [f'Admin accounts', "Auto firmware update", "Password policy", "Switch templates", "AP Security", "Switch Security", "WLAN Security"]
                all_scores = [admin_score, firmware_score, password_score, switch_template_score, ap_firmware_score, switch_firmware_score, wlan_score]

                # Max value is calculated as the length of the list "all_scores" * 10 so that it can be compared against the percentage values returned by max score.
                max_value = len(all_scores) * 10

                # Filter out scores that are 0
                filtered_data = [(label, score, color) for label, score, color in zip(all_labels, all_scores, colors) if score > 0]
                
                # Extract filtered labels, scores, and colors
                labels = [item[0] for item in filtered_data]
                scores = [item[1] for item in filtered_data]
                filtered_colors = [item[2] for item in filtered_data]

                total_value = sum(scores)
                missing_val = max_value - total_value

                if missing_val > 0:
                    labels.append("")  
                    scores.append(missing_val)
                    filtered_colors.append('#FFFFFF')  

                try:
                    with open('sec_audit_log.log', 'r') as file:
                        log = json.load(file)
                except (FileNotFoundError, json.JSONDecodeError):
                    log = {}

                if timestamp not in log:
                    log[timestamp] = {}

                for i, label in enumerate(all_labels):
                    score = all_scores[i]
                    match label:
                        case "Admin accounts":
                            log[timestamp][label] = {"score": score, "Accounts": failing_admins}
                        case "Auto firmware update":
                            log[timestamp][label] = {"score": score, "Autofirmware update": failing_sites}
                        case "Password policy":
                            log[timestamp][label] = {"score": score, "Password Policy": recommendations}
                        case "Switch templates":
                            log[timestamp][label] = {"score": score, "Switch Templates": switch_fail_log}
                        case "AP Security":
                            log[timestamp][label] = {"score": score, "AP Firmware": ap_firmware_recommendations}
                        case "Switch Security":
                            log[timestamp][label] = {"score": score, "Switch firmware": switch_firmware_versions}
                        case "WLAN Security":
                            log[timestamp][label] = {"score": score, "WLAN firmware": None}

                # Add missing value to log
                if missing_val > 0:
                    log[timestamp][""] = {"score": missing_val}

                with open('sec_audit_log.log', 'w') as file:
                    json.dump(log, file, indent=4)

                fig1, ax1 = plt.subplots(figsize=(18, 18))
                
                # Only create pie chart if there are scores to display
                if scores:
                    # Create pie chart with adjusted parameters to prevent overlap
                    wedges, texts, autotexts = ax1.pie(
                        scores, 
                        labels=labels, 
                        colors=filtered_colors,
                        autopct=lambda p: f'{p * sum(scores) / 100:.0f}', 
                        pctdistance=0.8,  
                        labeldistance=1,  
                        startangle=90, 
                        wedgeprops={'width': 0.4},
                        textprops={'fontsize': 28, 'fontweight': 'bold'}  
                    )
                    
                    # Style the labels with better positioning
                    for i, text in enumerate(texts):
                        text.set_fontsize(28)  
                        text.set_color('black')
                        text.set_fontweight('bold')
                        
                        # Add manual positioning for better spacing if needed
                        if labels[i]:  # Only adjust non-empty labels
                            x, y = text.get_position()
                            
                            # Adjust position slightly to reduce overlap
                            text.set_position((x * 1.05, y * 1.05))

                    # Style the percentage labels
                    for autotext in autotexts:
                        autotext.set_fontsize(36)  
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                else:
                    # If no scores to display, show a message
                    ax1.text(0, 0, "No scores to display", 
                            horizontalalignment='center', 
                            verticalalignment='center',
                            fontsize=24, 
                            fontweight='bold')
                
                # Center text showing total score
                ax1.text(0, 0, f"{total_value}/{max_value}", 
                        horizontalalignment='center', 
                        verticalalignment='center',
                        fontsize=56, 
                        fontweight='bold')
                
                ax1.axis('equal')

                col1.title("Mist org security audit")
                
                # Adjust layout to prevent clipping
                fig1.tight_layout(pad=2.0)
                st.pyplot(fig1)  

                with col2:
                    col2.title("Current issues")
                    st.subheader(f"Password security: {password_score}/10")
                    st.text(json_to_bullet_points(recommendations))
                    if st.button("Apply recommended password fixes", key=f'password_recommended_solution{timestamp}'):
                        update_password(api_response=backend.get_api('api.json'))
                        st.success("Password Fixes applied")
                        print("button pushed")
                    st.subheader(f"Auto firmware Update: {firmware_score}/10")
                    st.text(json_to_bullet_points(failing_sites))
                    if st.button("Apply recommended autoupgrade firmware fixes", key=f'firmware_recommended_solution{timestamp}'):
                        update_firmware(api_response=backend.get_api('api.json'))
                    st.subheader(f"Admin account security: {admin_score}/10")
                    st.text(json_to_bullet_points(failing_admins))
                    st.subheader(f"Switch template recommendations: {switch_template_score}/10")
                    st.text(json_to_bullet_points(switch_fail_log))
                    if st.button("Apply recommended switch template fixes", key=f'switch_template_recommended_solution{timestamp}'):
                        update_switch_templates(api_response=backend.get_api('api.json'))    
                    st.subheader(f"AP security: {ap_firmware_score}/10")
                    st.text(json_to_bullet_points(ap_firmware_recommendations))
                    if st.button("Upgrade all AP firmware to latest recommended version", key=f'apply_ap_firmware_upgrade{timestamp}'):
                        update_firmware(api_response=backend.get_site_api('api.json'))  
                        print("button pressed")
                    st.subheader(f"Switch security: {switch_firmware_score}/10")
                    st.text(json_to_bullet_points(switch_firmware_versions))
                    if st.button("Upgrade all switch firmware to latest recommended version", key=f'apply_switch_firmware_upgrade{timestamp}'):
                        update_firmware(api_response=backend.get_site_api('api.json'))  
                        print("button pressed")
                    st.subheader(f"WLAN Security: {wlan_score}/10")

                run_tests = False

            if st.button("Re-run test", key=f"rerun_button{timestamp}"):
                run_tests = True

    with tab2:
        col1, col2 = st.columns([1,1], gap='medium')
        with col1:
            try:
                with open('sec_audit_log.log', 'r') as p_log:
                    data = json.load(p_log)
                    keys = list(data.keys())

                    if len(keys) >= 2:
                        # Use second-to-last timestamp for "previous" scores
                        previous_timestamp = keys[-2]
                    elif len(keys) == 1:
                        # If only one entry, use it as "previous"
                        previous_timestamp = keys[-1]
                    else:
                        # No data available
                        st.error("No previous data available")
                        return

                    previous_data = data[previous_timestamp]

                    # Original labels and scores (same order as tab1)
                    all_p_labels = ['Admin accounts', "Auto firmware update", "Password policy", "Switch templates", "AP Security", "Switch Security", "WLAN Security"]
                    all_p_scores = []
                    
                    # Extract scores in the same order as tab1
                    for label in all_p_labels:
                        if label in previous_data:
                            score = previous_data[label].get('score', 0)
                            all_p_scores.append(score)
                        else:
                            all_p_scores.append(0)

                    # Filter out scores that are 0 (same logic as tab1)
                    filtered_p_data = [(label, score, color) for label, score, color in zip(all_p_labels, all_p_scores, colors) if score > 0]
                    
                    # Extract filtered labels, scores, and colors
                    p_labels = [item[0] for item in filtered_p_data]
                    p_scores = [item[1] for item in filtered_p_data]
                    filtered_p_colors = [item[2] for item in filtered_p_data]

                    p_total_value = sum(p_scores)
                    p_missing_val = max_value - p_total_value

                    # Only add the empty segment if there's missing value
                    if p_missing_val > 0:
                        p_labels.append("")  
                        p_scores.append(p_missing_val)
                        filtered_p_colors.append('#FFFFFF')  # White for missing value

                    # Create figure with larger size for better label spacing
                    fig2, ax2 = plt.subplots(figsize=(18, 18))
                    
                    # Only create pie chart if there are scores to display
                    if p_scores:
                        # Create pie chart with same parameters as tab1
                        wedges, texts, autotexts = ax2.pie(
                            p_scores, 
                            labels=p_labels, 
                            colors=filtered_p_colors,
                            autopct=lambda p: f'{p * sum(p_scores) / 100:.0f}', 
                            pctdistance=0.8,  
                            labeldistance=1,  
                            startangle=90, 
                            wedgeprops={'width': 0.4},
                            textprops={'fontsize': 28, 'fontweight': 'bold'}
                        )
                        
                        # Style the labels with better positioning
                        for i, text in enumerate(texts):
                            text.set_fontsize(28)  
                            text.set_color('black')
                            text.set_fontweight('bold')
                            
                            # Add manual positioning for better spacing if needed
                            if p_labels[i]:  # Only adjust non-empty labels
                                x, y = text.get_position()
                                text.set_position((x * 1.05, y * 1.05))

                        # Style the percentage labels
                        for autotext in autotexts:
                            autotext.set_fontsize(24)
                            autotext.set_color('white')
                            autotext.set_fontweight('bold')
                    else:
                        # If no scores to display, show a message
                        ax2.text(0, 0, "No previous scores to display", 
                                horizontalalignment='center', 
                                verticalalignment='center',
                                fontsize=24, 
                                fontweight='bold')
                    
                    # Center text showing total score
                    ax2.text(0, 0, f"{p_total_value}/{max_value}", 
                            horizontalalignment='center', 
                            verticalalignment='center',
                            fontsize=36, 
                            fontweight='bold')
                    
                    ax2.axis('equal')

                    col1.title("Previous Mist org security audit")
                    
                    # Adjust layout to prevent clipping
                    fig2.tight_layout(pad=2.0)
                    st.pyplot(fig2)

            except (FileNotFoundError, json.JSONDecodeError):
                st.error("No previous audit data found")

        with col2:
            try:
                with open('sec_audit_log.log', 'r') as p_log:
                    data = json.load(p_log)
                    keys = list(data.keys())

                    if len(keys) >= 2:
                        previous_timestamp = keys[-2]
                    elif len(keys) == 1:
                        previous_timestamp = keys[-1]
                    else:
                        st.error("No previous data available")
                        return

                    previous_data = data[previous_timestamp]

                    st.title("Previous issues")
                    
                    # Only show sections that have non-zero scores
                    if 'Password policy' in previous_data and previous_data['Password policy'].get('score', 0) > 0:
                        st.subheader("Password security")
                        st.text(json_to_bullet_points(previous_data['Password policy']))
                    
                    if 'Auto firmware update' in previous_data and previous_data['Auto firmware update'].get('score', 0) > 0:
                        st.subheader("Auto Firmware Update")
                        st.text(json_to_bullet_points(previous_data['Auto firmware update']))
                    
                    if 'Admin accounts' in previous_data and previous_data['Admin accounts'].get('score', 0) > 0:
                        st.subheader("Admin account security")
                        st.text(json_to_bullet_points(previous_data['Admin accounts']))
                    
                    if 'Switch templates' in previous_data and previous_data['Switch templates'].get('score', 0) > 0:
                        st.subheader("Switch template security")
                        st.text(json_to_bullet_points(previous_data['Switch templates']))
                    
                    if 'AP Security' in previous_data and previous_data['AP Security'].get('score', 0) > 0:
                        st.subheader("AP security")
                        st.text(json_to_bullet_points(previous_data['AP Security']))
                    
                    if 'Switch Security' in previous_data and previous_data['Switch Security'].get('score', 0) > 0:
                        st.subheader("Switch security")
                        st.text(json_to_bullet_points(previous_data['Switch Security']))
                  
                    if 'WLAN Security' in previous_data and previous_data['WLAN Security'].get('score', 0) > 0:
                        st.subheader("Switch security")

            except (FileNotFoundError, json.JSONDecodeError):
                st.error("No previous audit data found")

def switch_inventory():
    switch_firmware_score, switch_firmware_versions, switches = get_switch_firmware_versions()

    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[3]}")
        st.markdown("    - This page shows the organisations switching estate")
        st.markdown("    - Out of date firmware is highlighted in red")
        st.markdown("    - This data can be downloaded using the button below the chart")

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

    #firmware_styles = {
    #    '23.4R2': 'background-color: green',
    #}

    def highlight_row(row):
        #required_columns = ['Root password']

        styles = [''] * len(row)

        #if all(pd.notna(row[required_columns]) & (row[required_columns] != '')):
            #for col in required_columns:
                #col_index = row.index.get_loc(col)
                #styles[col_index] = 'background-color: red'

        switch_name = row['Model']  
        firmware_version = switch_firmware_dict.get(switch_name[:8], None)

        if firmware_version:
            firmware_cell_value = row['Firmware']

            if firmware_version != firmware_cell_value[:6]:
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
    switch_inv.columns = ['Model', 'Name', 'Firmware', 'Site_ID', 'Device ID']
    #switch_inv.columns = ['Model', 'Name', 'Firmware', 'Site_ID', 'Device ID', 'Root password']
    
    styled_switch_inv = switch_inv.style.apply(highlight_row, axis=1)
    
    df = st.dataframe(styled_switch_inv)

    csv = convert_for_download(switch_inv)

    st.download_button(
        label="Download Switch Inventory",
        data=csv,
        file_name='switch_inventory.csv'
    )

def ap_inventory():
    ap_firmware_score, ap_firmware_recommendations, access_points = get_ap_firmware_versions()

    ap_firmware_dict = {
        "AP45": "0.12",
        "AP34": "0.12",
        "AP24": "0.14",
        "AP64": "0.14",
        "AP43": "0.10",
        "AP63": "0.12",
        "AP43-FIPS": "0.10",
        "AP12": "0.12",
        "AP32": "0.12",
        "AP33": "0.12",
        "AP41": "0.12",
        "AP61": "0.12",
        "AP21": "0.8",
        "BT11": "0.8"
    }

    firmware_styles = {
        '0.12': 'background-color: yellow',
        '0.14': 'background-color: white',
        '0.10': 'background-color: orange',
        '0.8': 'background-color: red'
    }
    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[4]}")
        st.markdown("    - This page shows the organisations AP estate")
        st.markdown("    - Out of date firmware is highlighted in red")
        st.markdown("    - This data can be downloaded using the button below the chart")


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

def raw_logs():
    count = 0
    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[6]}")
        st.markdown("    - This page shows the audit logs used to generate tables and graphs from other pages")
        st.markdown("    - This data can be downloaded by scrolling to the bottom of the page and clicking download")

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
    # raw_data contains a Mist "perfect" password Policy which is then sent to the Mist cloud using a put request.
    raw_data = json.dumps({"password_policy": {"enabled": True,
                                "min_length": 16,
                                "requires_special_char": True,
                                "requires_two_factor_auth": True}})
    
    requests.put("{}/setting".format(api_response[0]), data=raw_data, headers=api_response[1])

def update_firmware(api_response):
    #returns a list or dictionary of device IDs
    upgrade_devices = get_device_ids_per_site()

    #loops over all devices in all sites and uses a post request to trigger an upgrade to the latest Mist recommended firmware.
    for site in upgrade_devices:
        for device in upgrade_devices[site]:
            requests.post("{0}{1}/devices/{2}/upgrade".format(api_response[0], site, device), headers=api_response[1]).json()

def update_switch_templates(api_response):
    return 0

def convert_for_download(df):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return csv_buffer.getvalue()

def histogram():
    json_file_path = 'sec_audit_log.log'

    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[2]}")
        st.markdown("    - This page shows a histogram of the sites security scores over time. All scores shown are from the audit logs, which can be viewed under the Raw Log File tab")
        st.markdown("    - The histogram is updated every time tests are run. So with an empty log file the entries will have hourly time stamps, for a more full log file these will become dates.")

    with open(json_file_path, 'r') as j:
        contents = json.load(j)  

    # Prepare arrays to hold scores and datetime keys
    datetimes = []
    admin_account_score_array = []
    auto_firmware_score_array = []
    switch_template_score_array = []
    password_policy_score_array = []

    for datetime_key, data in contents.items():
        datetimes.append(datetime_key)
        admin_account_score_array.append(data['Admin accounts']['score'])
        auto_firmware_score_array.append(data['Auto firmware update']['score'])
        switch_template_score_array.append(data['Switch templates']['score'])
        password_policy_score_array.append(data['Password policy']['score'])


    # Create DataFrame with datetime keys as index
    df = pd.DataFrame({
        'Admin Accounts': admin_account_score_array,
        'Auto Firmware Updates': auto_firmware_score_array,
        'Switch Templates': switch_template_score_array,
        'Password Policy': password_policy_score_array,
    }, index=pd.to_datetime(datetimes, format='%Y-%m-%d %H-%M-%S'))

    df = df.sort_index()
    df.iloc[::-1].reset_index(drop=True)

    st.subheader("Audit Scores Visualization")
    fig, ax = plt.subplots(figsize=(20,15))
    df.plot(kind='line',
        style=['.-','o--','o-','.--'],
        ax=ax,
        linewidth=3,           # thicker lines
        markersize=10,          # bigger markers
        grid=True,             # show grid
        colormap='tab10')

    plt.legend(fontsize=25)
    plt.xlabel("Date Time", fontsize=35, fontweight='bold')
    plt.ylabel("Score", fontsize=35, fontweight='bold')
    plt.title("Security Audit Scores Over Time",fontsize=35, fontweight='bold')
    plt.xticks(rotation=45, ha='right', fontsize=15)  # rotate for readability
    plt.tight_layout()

    st.pyplot(fig)

def wlan_settings():
    # Set sidebar drop down for navigation 
    with st.sidebar:
        st.markdown(f"# {list(page_names_to_funcs.keys())[5]}")
        st.markdown("Radio buttons represent True or False")


    wlans, score = get_wlans()

    #Render "wlans" variable as streamlit dataframe 
    st.dataframe(wlans)
    

if not os.path.exists('api.json'):
    page_names_to_funcs = {
        "Org settings": org_settings,
    }
else:
    page_names_to_funcs = {
        "Org settings": org_settings,
        "Pie Chart": pie_chart,
        "Histogram": histogram,
        "Switch inventory": switch_inventory,
        "AP inventory": ap_inventory,
        "WLAN Settings": wlan_settings,
        "Raw log files": raw_logs
    }


demo_name = st.sidebar.selectbox("Choose demo", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()