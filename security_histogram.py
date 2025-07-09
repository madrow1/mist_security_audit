import json
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


json_file_path = 'sec_audit_log.log'

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

# Sort by datetime ascending (optional)
df = df.sort_index()
df.iloc[::-1].reset_index(drop=True)

# Plot
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
