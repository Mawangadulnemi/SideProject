import datetime
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from langchain_community.chat_models import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda
from langchain.prompts import ChatPromptTemplate
from operator import itemgetter
import pprint


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# GET from Each Google Calandar List
def getting_events(calendar_id):
  schedule_data = {}
  """Shows basic usage of the Google Calendar API.
  Prints the start and name of the next 10 events on the user's calendar.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    # print("Getting the upcoming 10 events")
    calendar_list_entry = service.calendarList().get(calendarId=calendar_id).execute()
    # calendarId=calendar_id
    # print(f"- {calendar_list_entry['summary']}")
    # schedule_data[f"- {calendarId}"] = calendar_list_entry['summary']
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
      print("YOU ARE FREE")
      return

    for event in events:
      # print(f"event : {event}")
      start = event["start"].get("dateTime", event["start"].get("date"))
      schedule_data[start] = event["summary"]
      # print(start, event["summary"])
    return schedule_data

  except HttpError as error:
    print(f"An error occurred: {error}")



# Formatting Data from Each List contents
def format_doc(id_items):
  results = []
  for id in id_items:
    result = getting_events(id)
    # print(f"result:{result}")
    results.append(result)
  results = str(results)
  # print(results, type(results))
  return results


llm = ChatOpenAI(temperature =.1,streaming=True
)


prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
        """
        You are world best secretary.
        Use spare time to plan the optimal schedule according to the user's request.
        Never ask for more information.
        
        context : {context}
        """
        ),
        ("human", "{question}"),
    ]
)

chain = {
    "context": itemgetter("context"),
    "question":itemgetter("question"),
    } | prompt | llm 


# Calandar List i want to get info
id_items = ['primary',"dd9c4420a018b66990bd3c9d3b91768073d5a2311a09f90894170d471ae5cf33@group.calendar.google.com"]


context = format_doc(id_items)
recommended = chain.invoke({"context": context, "question": 
"""
BASED MY CONTEXT,  Make BEST schedule!!

My request:I want to go amuesment park with my girl freind in next week recommand specific date
"""
})


pprint.pprint(f"Google Calandar results : \n\n\n{context}")
pprint.pprint(f"Recomand Contents : \n\n\n{recommended.content}")
