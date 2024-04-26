from google_auth_oauthlib.flow import InstalledAppFlow
from google.cloud import storage

def authenticate_with_oauth(scopes):
    # your json config from google oauth
    client_secrets_file = 'config.json'

    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file,
        scopes=scopes
    )
    creds = flow.run_local_server(port=0)
    return creds

def list_gcs_buckets(project_id, credentials):
    storage_client = storage.Client(project=project_id, credentials=credentials)
    buckets = storage_client.list_buckets()
    return buckets

def main():
    scopes = ['https://www.googleapis.com/auth/devstorage.read_write']
    creds = authenticate_with_oauth(scopes)

    # here you would need to get user's projectid from the frontend
    project_id = 'ssomorgan'


    buckets = list_gcs_buckets(project_id, creds)
    for bucket in buckets:
        print(bucket.name)

if __name__ == '__main__':
    main()
