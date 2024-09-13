import requests
import subprocess
import os
import shutil
import json


def get_api_key():
    return os.getenv('API_KEY')

def get_site_url():
    return os.getenv('BASE_URL')

def get_stack_name():
    return os.getenv('STACK_NAME')

def get_build_number():
    return os.getenv('BUILD_NUMBER')

deptrack_api_key = get_api_key()
deptrack_baseurl = get_site_url()
# deptrack_api_key = "ENpnO6nU6JmjXGURJ7weXY7Ig4b9r9u0"
# deptrack_baseurl = "https://dt.secops-corp.cloudera.com/api"

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
        
        output_dir = "sboms/" + stack_name + "-" + stack_version
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

def merge_sbom_files(directory):

    files = os.listdir(directory)

    sbom_file_paths = find_sbom_files(directory)

    if not sbom_file_paths:
        print('No valid SBOM files found in the directory.')

    command = ['cyclonedx', 'merge', '--input-files'] + sbom_file_paths
    output_file = os.path.join(directory, 'merged-sbom.json')
    command += ['--output-file', output_file]

    try:
        print('merging')
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f'Successfully merged SBOM files into {output_file}')
        print('Output:', result.stdout)
        return output_file
    except subprocess.CalledProcessError as e:
        print('Failed to merge SBOM files.')
        print('Error:', e.stderr)
        print("error:")

def importSBOM(stack_name, build_number):
    download = DownloadSbom(stack_name, build_number)
    if download != 200:
        return "Unable to download SBOMs", 400
    # download.get(stack_name=stack_name, build_number=build_number)

    stack_version = build_number.split('-')[0]
    
    headers = {
        'X-API-Key': deptrack_api_key
    }

    try:
        url = deptrack_baseurl + "/v1/project/lookup?name=" + stack_name + "&version=" + stack_version
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print("Project present")
            uuid = response.json()['uuid']
            delete_url = deptrack_baseurl + "/v1/project/" + uuid
            delete_response = requests.delete(delete_url, headers=headers)
            print("project deleted")
    except Exception as e:
        print("An error occurred:", str(e))

    dir = "sboms/" + stack_name + "-" + stack_version

    output_file_merged = merge_sbom_files(dir)
    print(output_file_merged)

    url = deptrack_baseurl + "/v1/bom"
    files = {
        'autoCreate': True,
        'projectName': stack_name,
        'projectVersion': stack_version,
        'bom': (open(output_file_merged, 'rb'))
    } 

    response = requests.post(url, headers=headers, files=files)
    print("project created and bom uploaded")
    try:
        os.remove(output_file_merged)
        print(f'Merged SBOM file deleted: {output_file_merged}')
    except OSError as e:
        print(f'Error deleting merged SBOM file: {e.strerror}')

    for root, dirs, files in os.walk(dir):
        for file in files:
            project_file = file
            if stack_name == "CDH":
                if not file.endswith("binary.json"):
                    continue
            
            projectName = project_file.strip('.json')
            projectVersion = build_number
            
            print(f"file path - {os.path.join(root, project_file)}")

            print(project_file, file)
            files = {
                'autoCreate': True,
                'projectName': projectName,
                'projectVersion': projectVersion,
                'parentName': stack_name,
                'parentVersion': stack_version,
                'bom': (project_file, open(os.path.join(root, project_file), 'rb'))
            }

            response = requests.post(url, headers=headers, files=files)
            print("bom uploaded")
            print(response.text)

    try:
        shutil.rmtree(dir)
        print(f"Directory and contents removed: {dir}")
    except OSError as e:
        print(f"Error removing directory: {dir} - {e.strerror}")

    return "Stack uploaded on Dependency Track", 201
    

if __name__ == '__main__':

    getStacks()
    print(stacks)

    stack_name = get_stack_name()
    build_number = get_build_number()
    # stack_name = "CB"
    # build_number = "2.88.0-b125"

    print(f"Stack Name: {stack_name}")
    print(f"Build Number: {build_number}")

    importSBOM(stack_name, build_number)