from google_auth_oauthlib.flow import InstalledAppFlow
from google.cloud import storage

def authenticate_with_oauth(scopes):
    # your json config from google oauth
    client_secrets_file = 'config.json'

    # this will open a browser window to authenticate the user
    # you will need to change this auth flow to reflect your architecture (backend only/frontend+backend/ etc. )
    flow = InstalledAppFlow.from_client_secrets_file(
        client_secrets_file,
        scopes=scopes
    )
    creds = flow.run_local_server(port=0)
    return creds

def list_gcs_buckets(storage_client):
    buckets = storage_client.list_buckets()
    return buckets

def list_files_in_bucket(bucket):
    blobs = bucket.list_blobs()
    return blobs

def main():
    scopes = ['https://www.googleapis.com/auth/devstorage.read_only']
    creds = authenticate_with_oauth(scopes)

    # here you would need to get user's projectid from the frontend
    project_id = 'ssomorgan'

    storage_client = storage.Client(project=project_id, credentials=creds)
    buckets = list_gcs_buckets(storage_client)
    for bucket in buckets:
        print('-------------------')
        print('Bucket: ' + bucket.name)
        bucket = storage_client.get_bucket(bucket.name)
        blobs = list_files_in_bucket(bucket)
        print('Files/Folders:')
        for blob in blobs:
            print(blob.name)

if __name__ == '__main__':
    main()
