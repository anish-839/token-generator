import streamlit as st
import os
import tempfile
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

# Scopes you need
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar"
]

st.title("Google OAuth Token Generator for Desktop App")
st.write("Upload your Google API `credentials.json` (desktop application type) to generate a `token.json` file.")

# Important note for users
st.info("""
**For Desktop Application Credentials:**
- Keep your Google Cloud Console project type as "Desktop Application"
- This tool will generate a token.json that works with your desktop app
- The OAuth flow will open in a new browser tab/window
""")

uploaded_file = st.file_uploader("Upload credentials.json", type=["json"])

if uploaded_file:
    try:
        # Read and parse the credentials file
        credentials_data = json.loads(uploaded_file.read())
        
        # Check if it's desktop application credentials
        if 'installed' not in credentials_data:
            st.error("❌ This appears to be web application credentials. Please use desktop application credentials from Google Cloud Console.")
            st.write("In Google Cloud Console: Credentials → Create Credentials → OAuth 2.0 Client ID → **Desktop Application**")
        else:
            # Save the uploaded file to a temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as tmp:
                json.dump(credentials_data, tmp)
                creds_path = tmp.name
            
            st.success("✅ Desktop application credentials uploaded successfully!")
            
            # Show the client ID for reference
            client_id = credentials_data.get('installed', {}).get('client_id', 'Not found')
            st.write(f"**Client ID:** {client_id}")
            
            if st.button("Generate Token"):
                try:
                    with st.spinner("Starting OAuth flow..."):
                        # Create the flow for desktop app
                        flow = InstalledAppFlow.from_client_secrets_file(
                            creds_path, 
                            SCOPES
                        )
                        
                        # For Streamlit Cloud, we need to use run_console instead of run_local_server
                        st.info("🔗 **Authorization Required:** A new browser tab will open for authorization.")
                        
                        # Generate authorization URL manually for better control
                        flow.redirect_uri = 'http://localhost:8080'
                        auth_url, _ = flow.authorization_url(
                            access_type='offline',
                            include_granted_scopes='true'
                        )
                        
                        st.markdown(f"**Step 1:** [🚀 Click here to authorize your app]({auth_url})")
                        st.markdown("""
                        **Step 2:** After authorizing:
                        1. You'll see a page that says "Please copy this code..."
                        2. Copy the entire authorization code
                        3. Paste it in the field below
                        """)
                        
                        # Input for authorization code
                        auth_code = st.text_input(
                            "Paste the authorization code here:",
                            help="After clicking the authorization link above, copy and paste the code you receive"
                        )
                        
                        if auth_code.strip():
                            try:
                                # Exchange code for credentials
                                flow.fetch_token(code=auth_code.strip())
                                creds = flow.credentials
                                
                                # Create token data in the format expected by desktop apps
                                token_data = {
                                    'token': creds.token,
                                    'refresh_token': creds.refresh_token,
                                    'token_uri': creds.token_uri,
                                    'client_id': creds.client_id,
                                    'client_secret': creds.client_secret,
                                    'scopes': list(creds.scopes) if creds.scopes else []
                                }
                                
                                token_json = json.dumps(token_data, indent=2)
                                
                                st.success("🎉 OAuth successful! Your token.json is ready for your desktop app.")
                                
                                # Download button
                                st.download_button(
                                    label="📥 Download token.json",
                                    data=token_json,
                                    file_name="token.json",
                                    mime="application/json",
                                    help="Save this file in your desktop application's directory"
                                )
                                
                                # Show usage instructions
                                st.markdown("""
                                ### 📋 How to use this token in your desktop app:
                                
                                1. Save the downloaded `token.json` in the same directory as your desktop app
                                2. Use this code snippet to load the credentials:
                                
                                ```python
                                from google.oauth2.credentials import Credentials
                                
                                # Load saved credentials
                                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
                                
                                # Use with Gmail API
                                service = build('gmail', 'v1', credentials=creds)
                                ```
                                """)
                                
                                # Optional: Display token info (remove if security concern)
                                with st.expander("🔍 View token details (for debugging)"):
                                    st.json({k: v for k, v in token_data.items() if k != 'refresh_token'})
                                    
                            except Exception as e:
                                st.error(f"❌ Error exchanging authorization code: {e}")
                                st.write("Make sure you copied the complete authorization code.")
                        
                except Exception as e:
                    st.error(f"❌ Error starting OAuth flow: {e}")
                    
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file. Please upload a valid credentials.json file.")
    except Exception as e:
        st.error(f"❌ Error processing uploaded file: {e}")

# Cleanup temp file
if 'creds_path' in locals():
    try:
        os.unlink(creds_path)
    except:
        pass

# Instructions section
st.markdown("""
---
### 📖 Setup Guide:

#### 1. Google Cloud Console (keep as Desktop Application):
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Select your project
- Navigate to: **APIs & Services** → **Credentials**
- Your OAuth 2.0 Client should be type: **Desktop Application** ✅
- Download the `credentials.json` file

#### 2. OAuth Consent Screen:
- Make sure your OAuth consent screen is configured
- Add test users if your app is in testing mode
- Required scopes: Gmail API, Calendar API

#### 3. Generate Token:
- Upload your `credentials.json` above
- Click "Generate Token" and follow the authorization steps
- Download the resulting `token.json` for your desktop app

### ❓ Troubleshooting:
- **Error 400**: Check that your credentials.json is for a desktop application
- **Access denied**: Make sure you're using the same Google account that has access to the OAuth consent screen
- **Invalid grant**: The authorization code might have expired, try generating a new one
""")
