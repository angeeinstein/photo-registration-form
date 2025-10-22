# OAuth 2.0 Setup Guide for Google Drive

## Quick Solution: Use OAuth Credentials Instead of Service Account

### Step 1: Create OAuth 2.0 Client

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Credentials**
4. Click **+ CREATE CREDENTIALS** → **OAuth 2.0 Client ID**
5. Application type: **Web application**
6. Name: "Photo Registration Drive Access"
7. **Authorized redirect URIs**: Add `http://localhost:5000/oauth2callback` and your production URL
8. Click **Create**
9. **Download the JSON** file (this is your `client_secret.json`)

### Step 2: Get Your Refresh Token

Run this one-time script to get your refresh token:

```python
# save as get_drive_token.py
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
import os.path

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def main():
    creds = None
    
    # Check if we have saved credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    print("\n✅ Success! Your credentials are saved.")
    print(f"\n📝 Refresh Token: {creds.refresh_token}")
    print(f"\n📝 Access Token: {creds.token}")
    print("\nSave these in your .env file or database!")

if __name__ == '__main__':
    main()
```

### Step 3: Install Required Package

```bash
pip install google-auth-oauthlib
```

### Step 4: Run the Script

```bash
python get_drive_token.py
```

This will:
1. Open your browser
2. Ask you to sign in with YOUR Google account
3. Grant Drive access
4. Save a `token.pickle` file with your refresh token

### Step 5: Use the Token

Add to your `.env` file:
```
GOOGLE_OAUTH_CLIENT_ID=your_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret  
GOOGLE_OAUTH_REFRESH_TOKEN=your_refresh_token
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
```

Then the app will use YOUR Drive account (with your storage quota) instead of a service account!

---

## OR: Full Implementation with Popup (More Complex)

If you want the full popup OAuth flow where users click "Connect Drive" in the admin panel, that requires:

1. Frontend: Load Google Identity Services
2. Backend: OAuth callback endpoints
3. Database: Store tokens per admin user
4. Drive uploader: Use OAuth tokens instead of service account

Let me know if you want me to implement the full popup version!
