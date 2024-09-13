import requests
import threading
import os

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
    
def trigger_jenkins_build_import_stack(stack_name, build_number):

    jenkins_url = os.getenv('JENKINS_URL')
    job_name = os.getenv('JOB_NAME')
    username = os.getenv('USERNAME')
    api_token = os.getenv('API_TOKEN')
    # jenkins_url = "http://localhost:8100"
    # job_name = 'Import Stack'
    # username = 'hsarkar'
    # api_token = '11b872198319bc1d97c5c683afe7cdb645'

    job_url = f"{jenkins_url}/job/{job_name}/buildWithParameters"
    crumb_url = f"{jenkins_url}/crumbIssuer/api/json"
    crumb_response = requests.get(crumb_url, auth=(username, api_token))

    if crumb_response.status_code == 200:
        crumb_data = crumb_response.json()
        crumb = {crumb_data['crumbRequestField']: crumb_data['crumb']}

        parameters = {
            'stackName': stack_name,
            'buildNumber': build_number
        }
        
        response = requests.post(job_url, auth=(username, api_token), params=parameters, headers=crumb)
        
        if response.status_code == 201:
            print(f"Build triggered successfully for job {job_name}.")
        else:
            print(f"Failed to trigger build: {response.status_code} - {response.text}")
    else:
        print(f"Failed to get crumb: {crumb_response.status_code} - {crumb_response.text}")

def importall():

    getStacks()
    threads = []

    for stack in stacks.keys():
        thread = threading.Thread(target=import_stack, args=(stack,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    return "imported all master branches successfully", 201


def import_stack(stackname):
    url = "https://release.infra.cloudera.com/hwre-api/stackinfo?stack=" + stackname + "&build_type=dev"
    response = requests.get(url)

    if response.status_code != 200:
        return "Error in getting stack info", 400

    print(response.text)

    stackinfo_data = response.json()

    for build, details in stackinfo_data.items():
        if details['branch'] == 'master' or details['branch'] == 'cdpd-master' or details['branch'] == 'cfm-main':

            print(stackname, build)
            print(f"branch: {details['branch']}")

            stack_name=stackname
            build_number=details['last_sucessful_build']

            trigger_jenkins_build_import_stack(stack_name, build_number)


if __name__ == '__main__':

    importall()