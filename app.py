import streamlit as st
import os
import tempfile
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials

# Scopes you need
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

st.title("Google OAuth Token Generator")
st.write("Upload your Google API `credentials.json` to generate a `token.json` file.")

uploaded_file = st.file_uploader("Upload credentials.json", type=["json"])

if uploaded_file:
    # Save the uploaded file to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        tmp.write(uploaded_file.read())
        creds_path = tmp.name

    if st.button("Run OAuth Flow"):
        try:
            # Run OAuth in local browser
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                creds_path, SCOPES
            )
            creds = flow.run_local_server(port=0)

            # Save token.json
            token_path = "token.json"
            with open(token_path, "w") as token:
                token.write(creds.to_json())

            with open(token_path, "rb") as f:
                st.success("OAuth successful! Download your token.json below.")
                st.download_button(
                    "Download token.json",
                    f,
                    file_name="token.json",
                    mime="application/json"
                )

        except Exception as e:
            st.error(f"Error during OAuth: {e}")
