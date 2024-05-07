from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware
import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError, Forbidden
import os
from dotenv import load_dotenv

load_dotenv()

# Those are the LLM Graph Builder Google Oauth APP ! Not the user !
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:8000/oauth2callback'

SCOPES = ['https://www.googleapis.com/auth/devstorage.read_only']

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

oauth_config = {
    "web": {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uris": [REDIRECT_URI],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
}

@app.get('/')
async def index():
    return HTMLResponse('''<h1>GCS bucket demo</h1>
                        <form action="/set_project" method="post">
                            <label>GCP Project ID: </label>
                            <input type="text" name="project_id" required>
                            <input type="submit" value="Submit">
                        </form>''')

@app.post('/set_project')
async def set_project(request: Request, project_id: str = Form(...)):
    request.session['project_id'] = project_id
    return RedirectResponse(url='/authorize', status_code=303)

@app.get('/authorize')
async def authorize(request: Request):
    if 'project_id' not in request.session:
        return RedirectResponse(url='/')
    flow = google_auth_oauthlib.flow.Flow.from_client_config(oauth_config, scopes=SCOPES)
    flow.redirect_uri = REDIRECT_URI
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    request.session['state'] = state
    return RedirectResponse(url=authorization_url)

@app.get('/oauth2callback')
async def oauth2callback(request: Request):
    if 'project_id' not in request.session:
        return RedirectResponse(url='/')
    state = request.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_config(oauth_config, scopes=SCOPES, state=state)
    flow.redirect_uri = REDIRECT_URI
    flow.fetch_token(authorization_response=str(request.url))
    request.session['credentials'] = credentials_to_dict(flow.credentials)
    return RedirectResponse(url='/list_buckets')

@app.get('/list_buckets')
async def list_buckets(request: Request):
    if 'credentials' not in request.session or 'project_id' not in request.session:
        return RedirectResponse(url='/')
    try:
        storage_client = storage.Client(credentials=google.oauth2.credentials.Credentials(**request.session['credentials']), project=request.session['project_id'])
        bucket_list = '<h1>List of Buckets</h1>' + ''.join([f'<p>Bucket: {bucket.name}</p>' for bucket in storage_client.list_buckets()])
        return HTMLResponse(bucket_list)
    except Forbidden as e:
        error_message = f"<h1>Access to the bucket denied</h1><p>{e.message}</p>"
        return HTMLResponse(error_message)
    except GoogleAPIError as e:
        error_message = f"<h1>Error: </h1><p>{e.message}</p>"
        return HTMLResponse(error_message)

def credentials_to_dict(credentials):
    return {'token': credentials.token, 'refresh_token': credentials.refresh_token, 'token_uri': credentials.token_uri, 'client_id': credentials.client_id, 'client_secret': credentials.client_secret, 'scopes': credentials.scopes}

if __name__ == '__main__':
    import uvicorn

    # This is only for DEV ! (to be able to have oauth running on http instead of https), remove this in production!!
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    uvicorn.run(app, host='localhost', port=8000)
