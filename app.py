import streamlit as st
import os
import tempfile
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Scopes you need
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

st.title("Google OAuth Token Generator")
st.write("Upload your Google API `credentials.json` to generate a `token.json` file.")

# Important note for users
st.info("""
**Important Setup Steps:**
1. In your Google Cloud Console, add your Streamlit app URL to the authorized redirect URIs
2. The redirect URI should be: `https://your-app-name.streamlit.app/` (replace with your actual app URL)
3. Make sure your OAuth consent screen is properly configured
""")

uploaded_file = st.file_uploader("Upload credentials.json", type=["json"])

if uploaded_file:
    try:
        # Read and parse the credentials file
        credentials_data = json.loads(uploaded_file.read())
        
        # Save the uploaded file to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as tmp:
            json.dump(credentials_data, tmp)
            creds_path = tmp.name
        
        st.success("Credentials file uploaded successfully!")
        
        # Show the client ID for reference
        client_id = credentials_data.get('web', {}).get('client_id', 'Not found')
        st.write(f"**Client ID:** {client_id}")
        
        if st.button("Start OAuth Flow"):
            try:
                # Create the flow
                flow = Flow.from_client_secrets_file(
                    creds_path,
                    scopes=SCOPES
                )
                
                # Set the redirect URI to your Streamlit app URL
                # You'll need to replace this with your actual Streamlit app URL
                app_url = st.secrets.get("app_url", "https://your-app-name.streamlit.app/")
                flow.redirect_uri = app_url
                
                # Generate the authorization URL
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true'
                )
                
                st.success("Authorization URL generated!")
                st.markdown(f"**Step 1:** [Click here to authorize the app]({auth_url})")
                st.write("**Step 2:** After authorization, you'll be redirected back. Copy the authorization code from the URL.")
                
                # Input field for the authorization code
                auth_code = st.text_input("Enter the authorization code:", key="auth_code")
                
                if auth_code and st.button("Exchange Code for Token"):
                    try:
                        # Exchange the authorization code for credentials
                        flow.fetch_token(code=auth_code)
                        creds = flow.credentials
                        
                        # Convert credentials to JSON
                        token_data = {
                            'token': creds.token,
                            'refresh_token': creds.refresh_token,
                            'token_uri': creds.token_uri,
                            'client_id': creds.client_id,
                            'client_secret': creds.client_secret,
                            'scopes': creds.scopes
                        }
                        
                        token_json = json.dumps(token_data, indent=2)
                        
                        st.success("OAuth successful! Your token.json is ready.")
                        
                        # Download button
                        st.download_button(
                            label="Download token.json",
                            data=token_json,
                            file_name="token.json",
                            mime="application/json"
                        )
                        
                        # Display the token (optional - you might want to remove this for security)
                        with st.expander("View token.json content"):
                            st.json(token_data)
                            
                    except Exception as e:
                        st.error(f"Error exchanging code for token: {e}")
                        
            except Exception as e:
                st.error(f"Error creating OAuth flow: {e}")
                st.write("Make sure your credentials.json file is valid and contains 'web' client configuration.")
                
    except json.JSONDecodeError:
        st.error("Invalid JSON file. Please upload a valid credentials.json file.")
    except Exception as e:
        st.error(f"Error processing uploaded file: {e}")

# Additional instructions
st.markdown("""
---
### Setup Instructions:

1. **Google Cloud Console Setup:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a project or select an existing one
   - Enable the Gmail API and Calendar API
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Choose "Web application"
   - Add your Streamlit app URL to "Authorized redirect URIs"

2. **Download and Upload:**
   - Download the `credentials.json` file from Google Cloud Console
   - Upload it using the file uploader above

3. **OAuth Flow:**
   - Click "Start OAuth Flow"
   - Follow the authorization link
   - Copy the authorization code from the redirect URL
   - Paste it back here to get your token.json

### Troubleshooting:
- Make sure your app URL is added to authorized redirect URIs in Google Cloud Console
- The redirect URI must exactly match your Streamlit app URL
- Ensure your OAuth consent screen is properly configured
""")

# Clean up temp file
if 'creds_path' in locals():
    try:
        os.unlink(creds_path)
    except:
        pass
