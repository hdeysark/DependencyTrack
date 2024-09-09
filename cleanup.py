import requests
import datetime
import os 

def get_api_key():
    return os.getenv('API_KEY')

def get_site_url():
    return os.getenv('BASE_URL')

deptrack_api_key = get_api_key()
deptrack_baseurl = get_site_url()

def cleanup():

    print(deptrack_api_key)
    print(deptrack_baseurl)

    url = deptrack_baseurl + "/v1/project?page=1&size=1000"
    headers = {
        'X-API-Key': deptrack_api_key
    }

    testurl = deptrack_baseurl + "/version"
    response = esponse = requests.get(testurl, headers=headers)

    try:
        response = requests.get(url, headers=headers)
        print(response)
        if(response.status_code != 200):
            return "Cannot fetch project list for cleanup", 400
        
        data = response.json()

        for entry in data:
            if entry.get('lastBomImport'):
                last_bom_import_timestamp = entry.get('lastBomImport')
                last_bom_import_seconds = last_bom_import_timestamp / 1000
                last_bom_import_date = datetime.datetime.fromtimestamp(last_bom_import_seconds)
                current_date = datetime.datetime.now()
                time_difference = current_date - last_bom_import_date
                one_week = datetime.timedelta(minutes=1)

                if time_difference >= one_week:
                    print("Last BOM import is older than a week.")
                    uuid = entry.get('uuid')
                    print(uuid)
                    delete_url = deptrack_baseurl + "/v1/project/" + uuid
                    delete_response = requests.delete(delete_url, headers=headers)
                    print(delete_response)
                else:
                    print("Last BOM import is within a week.")

            # Do we need this?
            else:
                print("No info on last BOM import, so delete")
                uuid = entry.get('uuid')
                print(uuid)
                delete_url = deptrack_baseurl + "/v1/project/" + uuid
                delete_response = requests.delete(delete_url, headers=headers)
                print(delete_response)

        return "Success", 200

    except Exception as e:
        print("An error occurred:", str(e))
        return "Unable cleanup", 400
    

if __name__ == '__main__':
    cleanup()