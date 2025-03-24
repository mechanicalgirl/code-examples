import json
import sys

import requests

server = sys.argv[1]
token = sys.argv[2]

url = 'https://example.com/api'
response = requests.get(url)
text = response.json()

url = f"https://{server}/api/v1/statuses"
params = {'status': text}
headers = {'Authorization': f"Bearer {token}"}

resp = requests.post(url, data=params, headers=headers)
resp.raise_for_status()
