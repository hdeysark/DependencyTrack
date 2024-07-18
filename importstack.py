import requests
import threading
import subprocess
import os
import shutil
import datetime
import json


stacks = {
    'CDH': 'parcel',
    'CM': 'parcel',
    'CSA': 'parcel',
    'CSA-DH': 'parcel',
    'CEM': 'parcel',
    'CEM-AGENTS': 'parcel',
    'CEM-AGENTS-JAVA': 'parcel',
    'CFM': 'parcel',
    'KEYTRUSTEE': 'parcel'
}

def getStacks():
    try:
        response = requests.get('https://release.infra.cloudera.com/hwre-api/getstacks')
        data = response.json()['stacks']
        for stack_name in data:
            if stack_name not in stacks:
                stacks[stack_name] = 'container'
        
        return 200
    except requests.exceptions.RequestException as e:
        print('Could not get stacks')
        return 500

def DownloadSbom(stack_name, build_number):

    success = getStacks()
    if success != 200:
        return 400
    
    build_data = ''

    try:
        print("https://release.infra.cloudera.com/hwre-api/buildgbn?stack=" + stack_name + "&release_version=" + build_number)
        response = requests.get("https://release.infra.cloudera.com/hwre-api/buildgbn?stack=" + stack_name + "&release_version=" + build_number)
        print(response)

        if response.status_code != 200:
            print("Unable to fetch GBN from RE API")
            print({'stack': stack_name, 'version': build_number, 'message': 'Unable to fetch SBOM'})    
            return 400  
        
        build_data = response.json()
        print(build_data)
        
        if build_data == {}:
            print("Invalid stack or version")
            print({'stack': stack_name, 'build number': build_number, 'message': 'Invalid stack or build number'})
            return 400

    except Exception as e:
        print(e)
        print ({'stack': stack_name, 'build number': build_number, 'message': 'Unable to get SBOM'})
        return 400

    gbn = build_data['gbn']
    print(gbn)

    url = "https://cloudera-build-us-west-1.vpc.cloudera.com/s3/build/" + gbn + "/SBOM/"

    response = requests.get(url)
    if response.status_code == 200:
        if stacks[stack_name] == 'container':
            url = url + "containers/"
        else:
            url = url + "redhat8/"

        try:
            response = requests.get(url)
            print(url)
            if response.status_code != 200:
                print ({'stack': stack_name, 'build number': build_number, 'message': 'Unable to fetch SBOM from bucket'})
                return 400
        
        except Exception as e:
            print(e)
            print ({'stack': stack_name, 'build number': build_number, 'message': 'Unable to get SBOM'})
            return 400

        stack_version = build_number.split('-')[0]

        # os.makedirs(output_dir, exist_ok=True)
        
        output_dir = "src/sboms/" + stack_name + "-" + stack_version
        subprocess.run(["wget", "-np", "-P", output_dir, "-r", "-R", "index.html*", url])

        print ('The SBOMs have been downloaded locally')
        return 200
    
    else:
        return 400


def is_valid_json(file_path):
    try:
        with open(file_path, 'r') as file:
            json.load(file)
        return True
    except json.JSONDecodeError:
        return False
    

def find_sbom_files(directory):

    sbom_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                print(f'Found JSON file: {file_path}')  
                if is_valid_json(file_path):
                    sbom_files.append(file_path)
                    print(f'Valid JSON file: {file_path}')  
                else:
                    print(f'Invalid JSON file skipped: {file_path}')
    return sbom_files



def get_api_key():
    return os.getenv('API_KEY')

def get_site_url():
    return os.getenv('SITE_URL')

api_key = get_api_key()
site_url = get_site_url()

# Use the API key and site URL in your code
print(f"API Key: {api_key}")
print(f"Site URL: {site_url}")

getStacks()
print(stacks)