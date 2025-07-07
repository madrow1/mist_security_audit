
import json 

with open('sec_audit_log.log', 'r') as j:
    contents = json.load(j)

print(f"Number of entries: {len(contents)}")  # Should tell you how many rows to expect
