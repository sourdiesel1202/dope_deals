import json
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)
with open(f'{dir_path}/configs/project.json', 'r') as f:
    config = json.loads(f.read())
with open(config['credential_file'], 'r') as f:
    creds = json.loads(f.read())
