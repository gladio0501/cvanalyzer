# Google OAuth Setup Guide

This guide walks you through setting up Google OAuth authentication for CVAnalyzer.

## Quick Start

1. [Create Google OAuth App](#step-1-create-a-google-cloud-project)
2. [Get Credentials](#step-3-create-oauth-20-credentials)
3. [Configure Environment](#configuration)
4. [Test Login](#testing)

---

## Google OAuth Setup

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Enter project name: **CVAnalyzer**
4. Click **"Create"** and wait for project creation
5. Select your new project from the dropdown

### Step 2: Configure OAuth Consent Screen

1. In the left sidebar, navigate to:  
   **APIs & Services** → **OAuth consent screen**

2. **Choose User Type**:
   - **External**: For anyone with a Google account (recommended for testing)
   - **Internal**: Only for Google Workspace users

3. **Fill in App Information**:
   - **App name**: `CVAnalyzer`
   - **User support email**: Your email address
   - **Developer contact email**: Your email address
   - Click **"Save and Continue"**

4. **Add Scopes**:
   - Click **"Add or Remove Scopes"**
   - Select these scopes:
     - `userinfo.email`
     - `userinfo.profile`
     - `openid`
   - Click **"Update"** → **"Save and Continue"**

5. **Add Test Users** (for External apps in testing):
   - Click **"Add Users"**
   - Enter your email address
   - Click **"Save and Continue"**

6. **Review and Complete**:
   - Review your settings
   - Click **"Back to Dashboard"**

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**

2. Click **"Create Credentials"** → **"OAuth client ID"**

3. **Configure the OAuth client**:
   - **Application type**: Web application
   - **Name**: `CVAnalyzer Web Client`

4. **Add Authorized Redirect URIs**:
   
   For **Development**:
   ```
   http://localhost:5000/api/auth/callback/google
   ```
   
   For **Production** (add later):
   ```
   https://yourdomain.com/api/auth/callback/google
   ```

5. Click **"Create"**

6. **Save Your Credentials**:
   - A dialog will show your **Client ID** and **Client Secret**
   - **Copy both values immediately** - you'll need them!
   - You can also download the JSON file for backup

---

## Configuration

### Step 1: Create Environment File

```bash
cd /path/to/CVanalyzer
cp .env.example .env
```

### Step 2: Add Google OAuth Credentials

Edit `.env` file and add your credentials:

```env
# Google OAuth Credentials
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here

# JWT Secret Key (generate a random string)
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this

# Frontend URL
FRONTEND_URL=http://localhost:5173

# Other Required Variables
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=sqlite:///cvanalyzer.db
```

### Step 3: Generate JWT Secret

Generate a secure JWT secret key:

```bash
# Option 1: Using OpenSSL
openssl rand -hex 32

# Option 2: Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as your `JWT_SECRET_KEY` in `.env`.

---

## Testing

### Step 1: Start the Backend Server

```bash
cd /path/to/CVanalyzer
source venv/bin/activate
python app.py
```

The server should start on `http://localhost:5000`.

### Step 2: Test OAuth Endpoints

**Check if Google OAuth is configured:**

```bash
curl http://localhost:5000/api/auth/providers
```

Expected response:

```json
{
  "providers": [
    {
      "name": "google",
      "display_name": "Google"
    }
  ]
}
```

**Check auth service health:**

```bash
curl http://localhost:5000/api/auth/health
```

Expected response:

```json
{
  "status": "healthy",
  "configured_providers": ["google"],
  "jwt_enabled": true
}
```

### Step 3: Test Login Flow (Browser)

1. Open your browser to:
   ```
   http://localhost:5000/api/auth/login/google
   ```

2. You should be redirected to Google's login page

3. Sign in with your Google account

4. Grant permissions to CVAnalyzer

5. You'll be redirected back to your application with a JWT token

### Step 4: Test Protected Endpoint

After logging in, use the JWT token:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  http://localhost:5000/api/auth/me
```

Expected response:

```json
{
  "user": {
    "id": 1,
    "email": "your-email@gmail.com",
    "name": "Your Name",
    "profile_picture": "https://...",
    "oauth_provider": "google",
    "created_at": "2025-10-29T..."
  }
}
```

---

## Troubleshooting

### Common Issues

#### 1. "OAuth not initialized" Error

**Cause**: OAuth not properly configured in Flask app

**Solution**: Ensure you're initializing OAuth in your Flask app:

```python
from auth import init_oauth

app = Flask(__name__)
oauth = init_oauth(app)
```

#### 2. "Redirect URI Mismatch" Error

**Cause**: The callback URL doesn't match what's registered in Google Cloud Console

**Solution**:

- Check the exact URL in the error message
- Go to Google Cloud Console → Credentials
- Edit your OAuth 2.0 Client ID
- Ensure `http://localhost:5000/api/auth/callback/google` is listed
- Note: Port number, http/https, and path must match exactly

#### 3. "Access Blocked: This app's request is invalid"

**Cause**: OAuth consent screen not properly configured

**Solution**:

- Go to OAuth consent screen settings
- Ensure all required fields are filled
- For External apps in testing mode, add your email as a test user
- Save changes and try again

#### 4. "Client secret invalid" Error

**Solution**:

- Go to Google Cloud Console → Credentials
- Find your OAuth 2.0 Client ID
- Click to view details
- Generate a new client secret
- Update your `.env` file with the new secret
- Restart your application

#### 5. Missing Email or Profile Information

**Cause**: Insufficient OAuth scopes

**Solution**:

- Check OAuth consent screen → Scopes
- Ensure `openid`, `userinfo.email`, and `userinfo.profile` are selected
- If you changed scopes, revoke access at https://myaccount.google.com/permissions
- Try logging in again

#### 6. CORS Errors in Browser

**Solution**: Update CORS configuration in your Flask app:

```python
from flask_cors import CORS

CORS(app, 
     origins=['http://localhost:5173', 'http://localhost:5000'],
     supports_credentials=True)
```

### Enable Debug Logging

Add detailed logging to troubleshoot issues:

```python
# In your Flask app
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verification Checklist

Before requesting help, verify:

- [ ] Google OAuth app created in Google Cloud Console
- [ ] OAuth consent screen configured with all required fields
- [ ] Test user added (for External apps)
- [ ] Redirect URI configured: `http://localhost:5000/api/auth/callback/google`
- [ ] Client ID and Secret copied to `.env` file
- [ ] `.env` file loaded (check with `python-dotenv`)
- [ ] JWT secret key generated and set
- [ ] Database initialized (`python database.py`)
- [ ] Backend server running without errors
- [ ] Can access `/api/auth/providers` endpoint
- [ ] Can access `/api/auth/health` endpoint

---

## Production Deployment

### Security Checklist for Production

1. **Use HTTPS**: Google OAuth requires HTTPS for production
2. **Update Redirect URI**: Add production URL to Google Cloud Console
3. **Secure Secrets**: Never commit `.env` to version control
4. **Rotate Secrets**: Change JWT secret key regularly
5. **Token Expiration**: Set appropriate token expiration times
6. **Rate Limiting**: Add rate limiting to auth endpoints
7. **Monitoring**: Set up logging for auth failures
8. **Session Security**: Configure secure cookies:

```python
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    JWT_COOKIE_SECURE=True,
    JWT_COOKIE_CSRF_PROTECT=True
)
```

### Production Redirect URI

When deploying to production:

1. Go to Google Cloud Console → Credentials
2. Edit your OAuth 2.0 Client ID
3. Add your production redirect URI:
   ```
   https://yourdomain.com/api/auth/callback/google
   ```
4. Keep the localhost URI for local testing

---

## Resources

- **Google OAuth Documentation**: [OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- **Google Cloud Console**: https://console.cloud.google.com/
- **Manage App Permissions**: https://myaccount.google.com/permissions

---

## Need Help?

1. Check application logs for detailed error messages
2. Verify environment variables are loaded correctly
3. Use browser developer tools to inspect network requests
4. Check Google Cloud Console logs for OAuth errors
5. Ensure your Google account has the necessary permissions

---

**Last Updated**: October 2025  
**CVAnalyzer Version**: 2.0.0
