from flask import Flask, jsonify, json
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from flask_cors import CORS


app = Flask(__name__)
CORS(app)

credentials=None
status=True

api_service_name = "youtube"
api_version = "v3"

def cmp_items(a, b):
    if a['publishedAt'] > b['publishedAt']:
        return 1
    else:
        return -1


def month_converted(mNum):
    months=['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return months[mNum-1]


@app.route('/', methods=['GET'])
def index():

    response={}

    status = {"status":True}

    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json",scopes = [
                'https://www.googleapis.com/auth/youtube.readonly'
        ]
    )
    response['message']="Simple server is running"
    response['status']=True

    try:
        flow.run_local_server(port=7777, prompt='consent')
        credentials=flow.credentials

    except:
        print('Error occurred during Authorization---------------------------------------------------\n\n')
        status=False
        response['message']="Failed"
        response['status']=False
        response = jsonify(response)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    
    youtube = build(
            api_service_name, 
            api_version, 
            credentials=credentials
        )

# Channel Request ------------------------------------------------------------------------------------------------------

    channel_request = youtube.channels().list(
        part="snippet,contentDetails",
        mine=True
    )
    channel_response = channel_request.execute()

    channel={}
    channel['publishedAt']=channel_response['items'][0]['snippet']['publishedAt']
    channel['Title']=channel_response['items'][0]['snippet']['localized']['title']
    channel['Thumbnails']=channel_response['items'][0]['snippet']['thumbnails']

    response['channel']=channel
    
# Subs Request ------------------------------------------------------------------------------------------------------

    subscription_request = youtube.subscriptions().list(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50
    )
    subscription_response = subscription_request.execute()

    subs=[]
    for item in subscription_response['items']:
        entry={}
        entry['eventType']='sub'
        entry['title']=item['snippet']['title']
        entry['thumbnails']=item['snippet']['thumbnails']
        entry['publishedAt']=item['snippet']['publishedAt']
        subs.append(entry)

    while("nextPageToken" in subscription_response.keys()):
        request = youtube.subscriptions().list(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50,
        pageToken=subscription_response["nextPageToken"],
        )
        subscription_response = request.execute()

        for item in subscription_response['items']:
            entry={}
            entry['title']=item['snippet']['title']
            entry['thumbnails']=item['snippet']['thumbnails']
            entry['publishedAt']=item['snippet']['publishedAt']
            entry['publishedAtUTC']=item['snippet']['publishedAt']
            subs.append(entry)

    subs.sort(key=lambda x: x['publishedAt'])

    for i in range(len(subs)):
        utc=subs[i]['publishedAt']
        std=''
        std+=utc[8:10]
        std+=' '
        std+=month_converted(int(utc[5:7]))
        std+=' '
        std+=utc[0:4]
        subs[i]['publishedAt']=std
    
    response['events']=subs


    # Enable Access-Control-Allow-Origin
    print(type(response))
    json_object = json.dumps(response, indent = 4)
    with open("output.json", "w") as outfile:
        outfile.write(json_object)
        
    response = jsonify(response)
    
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response #returning key-value pair in json format
    # return "Yo"

if __name__ == "__main__":
    app.run(debug=True)


