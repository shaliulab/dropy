import requests
import yaml

with open("config.yaml", "r") as filehandle:
    config = yaml.load(filehandle, Loader=yaml.SafeLoader)

app_key = config["app_key"]
app_secret = config["app_secret"]


def authenticate():

    # build the authorization URL:
    authorization_url = "https://www.dropbox.com/oauth2/authorize?client_id=%s&response_type=code" % app_key

    # send the user to the authorization URL:
    print('Go to the following URL and allow access:')
    print(authorization_url)

    # get the authorization code from the user:
    authorization_code = input('Enter the code:\n')

    # exchange the authorization code for an access token:
    token_url = "https://api.dropboxapi.com/oauth2/token"
    params = {
        "code": authorization_code,
        "grant_type": "authorization_code",
        "client_id": app_key,
        "client_secret": app_secret
    }
    
    response = requests.post(token_url, data=params)
    return response

