import streamlit as st
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import tempfile
import os
from urllib.parse import urlparse, parse_qs

# Page config
st.set_page_config(
    page_title="Google OAuth Token Generator",
    page_icon="🔐",
    layout="wide"
)

st.title("🔐 Google OAuth Token Generator")
st.markdown("Generate OAuth tokens for Google APIs that work anywhere!")

# Scopes configuration
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar"
]

st.sidebar.header("📋 Configuration")
st.sidebar.write("**Scopes included:**")
for scope in SCOPES:
    st.sidebar.write(f"- {scope.split('/')[-1]}")

# Initialize session state
if 'credentials_uploaded' not in st.session_state:
    st.session_state.credentials_uploaded = False
if 'auth_url' not in st.session_state:
    st.session_state.auth_url = None
if 'flow' not in st.session_state:
    st.session_state.flow = None

# Step 1: Upload credentials file
st.header("📤 Step 1: Upload Credentials File")
st.info("Upload your `credentials.json` file from Google Cloud Console (Desktop Application type)")

uploaded_file = st.file_uploader(
    "Choose credentials.json file", 
    type="json",
    help="This should be a desktop application credentials file from Google Cloud Console"
)

if uploaded_file is not None:
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as tmp_file:
            credentials_data = json.loads(uploaded_file.getvalue().decode())
            json.dump(credentials_data, tmp_file)
            tmp_path = tmp_file.name
        
        # Verify it's desktop app credentials
        if 'installed' not in credentials_data:
            st.error("❌ This is not a desktop application credentials file")
            st.write("Please create Desktop Application credentials in Google Cloud Console")
            st.session_state.credentials_uploaded = False
        else:
            st.success("✅ Desktop application credentials verified")
            client_id = credentials_data['installed']['client_id']
            st.write(f"**Client ID:** `{client_id}`")
            st.session_state.credentials_uploaded = True
            st.session_state.credentials_path = tmp_path
            
    except json.JSONDecodeError:
        st.error("❌ Invalid JSON file")
        st.session_state.credentials_uploaded = False
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.session_state.credentials_uploaded = False

# Step 2: Generate authorization URL
if st.session_state.credentials_uploaded:
    st.header("🔗 Step 2: Authorization")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("🚀 Generate Authorization URL", type="primary"):
            try:
                # Create OAuth flow with manual redirect URI
                flow = Flow.from_client_secrets_file(
                    st.session_state.credentials_path,
                    scopes=SCOPES,
                    redirect_uri='http://localhost:8080'
                )
                
                # Generate authorization URL
                auth_url, _ = flow.authorization_url(
                    access_type='offline',
                    include_granted_scopes='true'
                )
                
                st.session_state.auth_url = auth_url
                st.session_state.flow = flow
                
            except Exception as e:
                st.error(f"❌ Error generating URL: {str(e)}")
    
    with col2:
        if st.session_state.auth_url:
            st.success("✅ Authorization URL generated!")
    
    # Display authorization instructions
    if st.session_state.auth_url:
        st.subheader("🌐 Authorization Instructions")
        
        # Display the clickable link
        st.markdown(f"**1. Click this authorization link:**")
        st.markdown(f"[🔗 **AUTHORIZE APPLICATION**]({st.session_state.auth_url})")
        
        st.markdown("**2. After authorizing:**")
        st.write("- You'll be redirected to a localhost page (which won't load)")
        st.write("- **Copy the entire URL** from your browser's address bar")
        st.write("- The URL will look like: `http://localhost:8080/?code=AUTHORIZATION_CODE&scope=...`")
        
        # Step 3: Process authorization code
        st.header("📥 Step 3: Complete Authorization")
        
        redirect_url = st.text_input(
            "Paste the full redirect URL here:",
            placeholder="http://localhost:8080/?code=...",
            help="Paste the complete URL you were redirected to after authorization"
        )
        
        if redirect_url and st.button("🎯 Generate Token", type="primary"):
            try:
                # Extract authorization code from URL
                parsed_url = urlparse(redirect_url)
                query_params = parse_qs(parsed_url.query)
                
                if 'code' not in query_params:
                    st.error("❌ No authorization code found in URL")
                else:
                    auth_code = query_params['code'][0]
                    st.write(f"📝 Extracted authorization code: `{auth_code[:20]}...`")
                    
                    # Exchange code for credentials
                    with st.spinner("🔄 Exchanging authorization code for tokens..."):
                        st.session_state.flow.fetch_token(code=auth_code)
                        creds = st.session_state.flow.credentials
                        
                        # Create token data
                        token_data = {
                            'token': creds.token,
                            'refresh_token': creds.refresh_token,
                            'token_uri': creds.token_uri,
                            'client_id': creds.client_id,
                            'client_secret': creds.client_secret,
                            'scopes': list(creds.scopes)
                        }
                        
                        # Display success and download
                        st.success("🎉 Token generated successfully!")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Token Details:**")
                            st.write(f"- Scopes: {len(token_data['scopes'])} authorized")
                            st.write(f"- Refresh token: {'✅ Yes' if token_data['refresh_token'] else '❌ No'}")
                            st.write(f"- Client ID: `{creds.client_id}`")
                        
                        with col2:
                            # Create download button
                            token_json = json.dumps(token_data, indent=2)
                            st.download_button(
                                label="📥 Download token.json",
                                data=token_json,
                                file_name="token.json",
                                mime="application/json"
                            )
                        
                        # Display token preview
                        with st.expander("👁️ Preview token.json"):
                            st.json(token_data)
                        
                        # Usage instructions
                        st.header("💻 Usage in Your Application")
                        st.code("""
# How to use the downloaded token.json in your application
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Load the token
creds = Credentials.from_authorized_user_file('token.json', SCOPES)

# Refresh if expired
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
    
    # Save refreshed credentials back to file
    with open('token.json', 'w') as token_file:
        token_file.write(creds.to_json())

# Build services
gmail_service = build('gmail', 'v1', credentials=creds)
calendar_service = build('calendar', 'v3', credentials=creds)
                        """, language="python")
                        
            except Exception as e:
                st.error(f"❌ Error generating token: {str(e)}")
                st.write("Make sure you pasted the complete redirect URL")

# Sidebar info
st.sidebar.header("ℹ️ About")
st.sidebar.write("""
This tool generates OAuth tokens for Google APIs that work in any environment:

**Why this approach?**
- Works in deployed Streamlit apps
- No redirect URI restrictions
- Manual process ensures compatibility
- Generates refresh tokens for long-term use

**Requirements:**
- Desktop Application credentials from Google Cloud Console
- Google APIs enabled in your project
""")

st.sidebar.header("🔧 Setup Guide")
with st.sidebar.expander("📖 Google Cloud Console Setup"):
    st.write("""
1. Go to Google Cloud Console
2. Create/select your project
3. Enable APIs (Gmail, Calendar, etc.)
4. Go to Credentials → Create Credentials
5. Choose "OAuth 2.0 Client ID"
6. Select "Desktop Application"
7. Download the JSON file
8. Upload it here!
    """)

# Footer
st.markdown("---")
st.markdown("🔒 **Security Note:** This process happens entirely in your browser. No credentials are stored on any server.")

# Cleanup temp files on script completion
if 'credentials_path' in st.session_state and os.path.exists(st.session_state.credentials_path):
    try:
        os.unlink(st.session_state.credentials_path)
    except:
        pass
