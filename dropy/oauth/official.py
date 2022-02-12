#!/usr/bin/env python3

# Based on https://raw.githubusercontent.com/dropbox/dropbox-sdk-python/main/example/oauth/commandline-oauth.py

import argparse
import json
import dropbox
from dropbox import DropboxOAuth2FlowNoRedirect

'''
This example walks through a basic oauth flow using the existing long-lived token type
Populate your app key and app secret in order to run this locally
'''


def get_parser(ap):
    if ap is None:
        ap = argparse.ArgumentParser()
    ap.add_argument("--app-key", dest="app_key", default=None)
    ap.add_argument("--app-secret", dest="app_secret", default=None)
    return ap


def read_config():
    raise NotImplementedError


def get_credential(args, credential):
    if getattr(args, credential) is None:
        config = read_config()
        value = getattr(config, credential)

    else:
        value = getattr(args, credential)

    return value


def get_credentials(args):

    app_key = get_credential(args, "app_key")
    app_secret = get_credential(args, "app_secret")
    return app_key, app_secret


#def get_access_token(app_key, app_secret):
#
#    auth_flow = DropboxOAuth2FlowNoRedirect(app_key, app_secret, token_access_type="legacy")
#
#    authorize_url = auth_flow.start()
#    print("1. Go to: " + authorize_url)
#    print("2. Click \"Allow\" (you might have to log in first).")
#    print("3. Copy the authorization code.")
#    auth_code = input("Enter the authorization code here: ").strip()
#
#    try:
#        oauth_result = auth_flow.finish(auth_code)
#    except Exception as e:
#        print('Error: %s' % (e,))
#        exit(1)
#
#    return oauth_result.access_token


def get_access_token(*args, **kwargs):
    with open("/etc/dropbox.conf", "r") as filehandle:
        token = json.load(filehandle)["token"]
    return token

def authenticate(**kwargs):

    access_token = get_access_token(**kwargs)

    with dropbox.Dropbox(oauth2_access_token=access_token) as dbx:
        dbx.users_get_current_account()
        print("Successfully set up client!")

def main(ap=None, args=None):

    if args is None:
        ap = get_parser(ap)
        args = ap.parse_args()

    app_key, app_secret = get_credentials(args)
    authenticate(app_key, app_secret)
