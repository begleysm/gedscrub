import sys
import os
import readline
import argparse
from urllib.parse import urlparse
from urllib.request import urlretrieve

import re
import requests
import mimetypes
from collections import defaultdict

USERNAME = "Rebeccagriffin54"
PASSWORD = "1alivia"
GEDCOM_FILE = r"/home/sean/Desktop/Family_Tree/GEDCOM/ancestry_Griffin-Family-Tree_2019-04-14.ged"
OUTPUT_DIRECTORY = r"/home/sean/Desktop/Family_Tree/Test"
DOWNLOAD_LIST = ["http://trees.ancestry.com/rd?f=image&guid=85fa8251-ab03-456b-9c5c-1d3313a9beb7&tid=14751255&pid=1146", "http://trees.ancestry.com/rd?f=image&guid=7b7d6f6f-ef80-45e2-bdbe-050557d91117&tid=14751255&pid=1155", "http://trees.ancestry.com/rd?f=image&guid=c3eaed48-530f-41c9-a57d-a1584fa8b667&tid=14751255&pid=1168"]
NAMESPACE = "1093"

def start_session(username, password):
    """
    Starts a session against the specified Ancestry website. Checks login was succesful.

    Returns the session.
    """

    session = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    session.headers.update(headers)

    login_url = 'https://www.ancestry.com/account/signin/frame/authenticate'
    referer_url = 'https://www.ancestry.com/account/signin/frame?'
    payload = {
        'action': login_url,
        'username': username,
        'password': password,
    }

    response = session.post(login_url, data=payload, headers={'referer': referer_url})
    
    if check_if_logged_in(response) == True:
        return session
    else:
        raise LoginError()

def check_if_logged_in(response):
    if (response.status_code != 200):
        return False
    if ('"status":"invalidCredentials"' in response.text):
        return False
    return True

### MAIN ###

#login
"""
try:
    session = start_session(USERNAME, PASSWORD)
except:
    print("There was a problem when logging into Ancestry.com. Perhaps check your details and try again.")
    print("Aborting.")
    #return
else:
    print("Login successful.")
"""

    #reformat GEDCOM FILE URL to target URL
reformatted_download_list = ["", "", ""]
for i in range(len(DOWNLOAD_LIST)):
    parsed = urlparse(DOWNLOAD_LIST[i])
    components = re.split(r'=|-|&', parsed.query)
    reformatted_download_list[i] = parsed.scheme + "://mediasvc.ancestry.com/v2/image/namespaces/" + NAMESPACE + "/media/" + components[3] + "-" + components[4] + "-" + components[5] + "-" + components[6] + "-" + components[7] + "?client=TreesUI"
    print(reformatted_download_list[i])
    #reformatted_download_list = ["https://mediasvc.ancestry.com/v2/image/namespaces/1093/media/42ef720d-d909-4b0a-b06c-06a848de5628?client=TreesUI", "https://mediasvc.ancestry.com/v2/image/namespaces/1093/media/ffa13d5c-cc93-4ac8-8b52-cc78302fc5af?client=TreesUI", "https://mediasvc.ancestry.com/v2/image/namespaces/1093/media/ae82324f-f411-4e6b-a119-a6fa9a63eff4?client=TreesUI"]

    #download 3 test images
"""
    image_download = session.get(reformatted_download_list[0], stream=True)
    with open(OUTPUT_DIRECTORY + "/" + "0.jpg", 'wb') as f:
                    for chunk in image_download.iter_content(1024):
                        f.write(chunk)

    image_download = session.get(reformatted_download_list[1], stream=True)
    with open(OUTPUT_DIRECTORY + "/" + "1.jpg", 'wb') as f:
                    for chunk in image_download.iter_content(1024):
                        f.write(chunk)

    image_download = session.get(reformatted_download_list[2], stream=True)
    with open(OUTPUT_DIRECTORY + "/" + "2.jpg", 'wb') as f:
                    for chunk in image_download.iter_content(1024):
                        f.write(chunk)
"""

