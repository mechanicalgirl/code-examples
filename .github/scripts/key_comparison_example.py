import base64
import difflib
import json
import os
import subprocess
import sys
from urllib.request import urlopen


api_url = 'https://www.example.com/path/to/publickeys/'
rootdir = os.getcwd()
key_source_file = rootdir + '/path/to/keyfile/main.tf'

# generate a list of current keys based on what's in the main branch
try:
    current_keys = []
    f = open(key_source_file, 'r+')
    lines = f.readlines()
    for line in lines:
        if line.lstrip().startswith('"'):
            key = line.lstrip().split('"')[1]
            current_keys.append(key)
except Exception as e:
    sys.exit(e)

# get the keys from the API endpoint
with urlopen(api_url) as response:
    body = response.read()
try:
    remote_certs = json.loads(body)
except Exception as e:
    sys.exit(e)
new_keys = []
for k, v in remote_certs.items():
    new_keys.append(k)

if current_keys != new_keys:
    for k in new_keys:
        # Generate file pointers for certificate files to be used below
        certfile = f'/tmp/{k}_cert.pem'
        pubkeyfile = f'/tmp/{k}_pubkey.pem'

        # Replace any extraneous line break indicators so that the certificate converts correctly
        cert = remote_certs[k]
        cert_content = cert.replace('\n', '')
        cert_content = cert_content.replace('-----BEGIN CERTIFICATE-----', '-----BEGIN CERTIFICATE-----\n')
        cert_content = cert_content.replace('-----END CERTIFICATE-----', '\n-----END CERTIFICATE-----')

        # Copy the certificate value into a temporary .pem file
        with open(certfile, "w+") as f:
            f.write(cert_content)

        # Create the public key based off the certificate.
        # This would be the equivalent of running:
        # openssl x509 -pubkey -noout -in cert.pem > pubkey.pem
        f = open(pubkeyfile, "w+")
        ossl = subprocess.run(['openssl','x509','-pubkey','-noout', '-in', certfile], stdout=f)
        f.close()

        # Base64 encode the key to in preparation for storing in the Terraform dictionary
        f = open(pubkeyfile, "rb")
        keybyte = f.read() # returns a bytes object
        # Base64 encode the bytes object
        base = base64.b64encode(keybyte)

        # Decode to convert to string
        base_decode = base.decode()
        # Convert to a string so that it can be written into the terraform file:
        itemline = f'      "{k}" = "{base_decode}"\n'

        # Append items - this will be the list used to replace the dictionary in the source file.
        tfitems.append(itemline)

# write the new terraform file
# Open key_source_file
with open(key_source_file, 'r') as f:
    data = f.readlines()

# Identify and replace dictionary items
for line in data:
    if line.lstrip().startswith('"'):
        num = data.index(line)
        try:
            data[num] = tfitems[0]
            tfitems.pop(0)
        except Exception as e:
            print(f"Not a token: {line}")

# Overwrite and close the file
with open(key_source_file, 'w') as f:
    f.writelines(data)
