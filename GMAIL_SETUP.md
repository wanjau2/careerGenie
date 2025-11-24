# Gmail Integration Setup Guide

This guide explains how to set up Gmail API integration for automatic job application status tracking.

## Overview

The Gmail integration allows Career Genie to:
- Read job-related emails from users' Gmail accounts (read-only access)
- Automatically detect application status updates (rejections, interviews, offers)
- Match emails to existing applications and update statuses
- Provide automatic tracking without manual status updates

## Prerequisites

- Google Cloud Platform account
- Gmail account for testing
- Backend server running with environment variables configured

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Name it something like "Career Genie Email Integration"

## Step 2: Enable Gmail API

1. In your Google Cloud project, go to **APIs & Services > Library**
2. Search for "Gmail API"
3. Click **Enable**

## Step 3: Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose **External** user type (unless you have Google Workspace)
3. Fill in the required information:
   - **App name**: Career Genie
   - **User support email**: Your email
   - **Developer contact email**: Your email
4. Click **Save and Continue**

### Add Scopes

1. Click **Add or Remove Scopes**
2. Add the following scope:
   - `https://www.googleapis.com/auth/gmail.readonly` (Read-only Gmail access)
3. Click **Update** then **Save and Continue**

### Add Test Users (for development)

1. Click **Add Users**
2. Add email addresses that will test the integration
3. Click **Save and Continue**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services > Credentials**
2. Click **Create Credentials > OAuth client ID**
3. Choose **Web application**
4. Configure:
   - **Name**: Career Genie Backend
   - **Authorized JavaScript origins**:
     - `http://localhost:8000`
     - `https://your-production-domain.com` (for production)
   - **Authorized redirect URIs**:
     - `http://localhost:8000/api/email/oauth2callback`
     - `https://your-production-domain.com/api/email/oauth2callback` (for production)
5. Click **Create**
6. **Download the JSON file** - this is your credentials file

## Step 5: Set Up Credentials File

1. Create a `credentials` directory in the backend:
   ```bash
   mkdir -p /home/Root/Desktop/projects/CareerGenie/backend/credentials
   ```

2. Move the downloaded JSON file to this directory:
   ```bash
   mv ~/Downloads/client_secret_*.json /home/Root/Desktop/projects/CareerGenie/backend/credentials/gmail_credentials.json
   ```

3. Add to `.gitignore` (if not already there):
   ```
   credentials/
   *.json
   ```

## Step 6: Configure Environment Variables

Add to your `.env` file:

```env
# Gmail Integration
GMAIL_CREDENTIALS_FILE=credentials/gmail_credentials.json
GMAIL_REDIRECT_URI=http://localhost:8000/api/email/oauth2callback

# For production, use:
# GMAIL_REDIRECT_URI=https://your-domain.com/api/email/oauth2callback
```

## Step 7: Test the Integration

### Start the Backend

```bash
cd /home/Root/Desktop/projects/CareerGenie/backend
source venv/bin/activate  # if using virtual environment
python app.py
```

### Test OAuth Flow

1. **Get Authorization URL**:
   ```bash
   curl -X POST http://localhost:8000/api/email/connect/gmail \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json"
   ```

2. The response will contain an `authorizationUrl`
3. Open this URL in a browser
4. Sign in with a Gmail account (must be a test user if in development)
5. Grant permissions
6. You'll be redirected back and see "Gmail Connected Successfully!"

### Test Email Scanning

```bash
curl -X POST http://localhost:8000/api/email/scan \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "daysBack": 7,
    "maxResults": 50
  }'
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/email/status` | GET | Get integration status |
| `/api/email/connect/gmail` | POST | Initiate OAuth flow |
| `/api/email/oauth2callback` | GET | OAuth callback (automatic) |
| `/api/email/disconnect` | POST | Disconnect Gmail |
| `/api/email/toggle` | POST | Enable/disable scanning |
| `/api/email/scan` | POST | Manually scan emails |
| `/api/email/test` | GET | Test connection |

## How Email Parsing Works

The system uses pattern matching to detect job application statuses:

### Status Detection Patterns

- **Rejected**: "regret to inform you", "not moving forward", "other candidates"
- **Interview Scheduled**: "schedule an interview", "invite you to interview"
- **Under Review**: "reviewing your application", "application received"
- **Offer Received**: "pleased to offer", "congratulations", "offer letter"
- **Interviewed**: "thank you for interview", "enjoyed speaking with you"

### Matching Emails to Applications

Emails are matched to applications based on:
1. Company name (extracted from sender domain or email body)
2. Job title (extracted from subject or body)
3. Timing (recent applications more likely to match)

Minimum match score of 3 is required for confident matching.

## Security Considerations

### User Data Privacy

- **Read-only access**: Users grant only `gmail.readonly` scope
- **No email storage**: Email content is never stored in the database
- **Temporary processing**: Emails are processed in memory and discarded
- **Audit trail**: All status updates include timestamp and source

### Token Management

- Access tokens are encrypted in database
- Refresh tokens allow automatic renewal
- Users can disconnect at any time
- Credentials are revoked on disconnect

### Rate Limiting

Google Gmail API has quotas:
- **Per-user limit**: 250 quota units/second
- **Daily limit**: 1 billion quota units/day
- Each email fetch = ~5 quota units
- Scanning 100 emails = ~500 units

Recommended scanning frequency: Every 6-12 hours for active users

## Production Deployment

### Before Publishing

1. **Verify OAuth consent screen**:
   - Complete all required fields
   - Add privacy policy URL
   - Add terms of service URL
   - Upload app logo

2. **Submit for verification** (if needed):
   - Go to OAuth consent screen
   - Click "Submit for verification"
   - Wait for Google approval (can take several weeks)

3. **Update redirect URIs**:
   - Add production domain to authorized redirect URIs
   - Update `GMAIL_REDIRECT_URI` environment variable

### Monitoring

Track these metrics:
- OAuth connection success rate
- Email scan frequency
- Status update accuracy
- API quota usage
- User disconnect rate

## Troubleshooting

### "Access blocked: This app's request is invalid"

**Cause**: OAuth consent screen not properly configured

**Solution**:
1. Check OAuth consent screen is published
2. Verify redirect URI matches exactly (including http/https)
3. Add test users if still in development

### "invalid_grant" error

**Cause**: Refresh token expired or revoked

**Solution**:
1. User needs to reconnect Gmail integration
2. Ensure refresh token is properly saved

### No emails found

**Cause**: Search query too restrictive or no matching emails

**Solution**:
1. Check date range (increase `daysBack`)
2. Verify user has job-related emails
3. Review search query patterns in `gmail_service.py`

### Status not updating

**Cause**: Low confidence score or no matching application

**Solution**:
1. Check email parsing patterns in `email_parser_service.py`
2. Verify application exists in database
3. Review matching algorithm threshold

## Resources

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Gmail API Python Quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)

## Support

For issues or questions:
1. Check backend logs: `backend/logs/app.log`
2. Review Gmail API quota usage in Google Cloud Console
3. Test OAuth flow with curl commands above
4. Contact development team with error details
