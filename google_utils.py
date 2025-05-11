# google_utils.py
import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from datetime import date

#––– Internals –––
def _connect(sheet_name):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )
    client = gspread.authorize(creds)
    return client.open("v4_resources").worksheet(sheet_name)

#––– History sheet (“News-hist”) –––
def load_history():
    ws = _connect("News-hist")
    df = pd.DataFrame(ws.get_all_records())
    return df

def append_history(week_tag, payload):
    ws = _connect("News-hist")
    # Build a flat row from payload + captions
    row = {
      "week": week_tag,
      **{k: payload.get(k,"") for k in ["title","events-prof","events-pers",
                                        "gratitude","productivity","up_next","facts","weekly"]}
    }
    # six image captions:
    for i, img in enumerate(payload.get("fact_images",[]), start=1):
        row[f"fact{i}_caption"] = img.get("caption","")
    # write it
    df = load_history()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    set_with_dataframe(ws, df)

#––– Subscribers sheet (“News-subs”) –––
def load_subscribers():
    ws = _connect("News-subs")
    return pd.DataFrame(ws.get_all_records())

def add_subscriber(email):
    ws = _connect("News-subs")
    df = load_subscribers()
    today = date.today().isoformat()
    if email in df["email"].values:
        st.warning(f"{email} is already subscribed.")
        return
    df = pd.concat([df, pd.DataFrame([{"email":email,"subscribed_date":today}])],
                   ignore_index=True)
    set_with_dataframe(ws, df)
    st.success(f"Added {email}.")

def remove_subscriber(email):
    ws = _connect("News-subs")
    df = load_subscribers()
    if email not in df["email"].values:
        st.warning(f"{email} was not in the list.")
        return
    df = df[df["email"] != email]
    set_with_dataframe(ws, df)
    st.success(f"Removed {email}.")