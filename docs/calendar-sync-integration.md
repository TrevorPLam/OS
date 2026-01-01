# Calendar Sync Integration Documentation

## Overview

The Calendar Sync feature enables staff users to connect their external calendars (Google Calendar, Microsoft Outlook) to ConsultantPro for automatic bi-directional synchronization of appointments.

**Status:** ✅ Complete (Sprint 2)

## Features

### Core Capabilities

1. **OAuth Authentication**
   - Google Calendar OAuth 2.0 integration
   - Microsoft Outlook/Office 365 OAuth 2.0 integration
   - Secure token storage and automatic refresh

2. **Bi-Directional Sync**
   - Pull external calendar events into ConsultantPro
   - Push internal appointments to external calendar
   - Incremental sync (Google: sync tokens, Microsoft: delta links)
   - Configurable sync window (default: 30 days past/future)

3. **Conflict Resolution**
   - Last-modified-wins strategy
   - Preserves data integrity across systems
   - Graceful handling of sync failures

4. **Sync Management**
   - Manual sync trigger
   - Automatic background sync
   - Connection enable/disable toggle
   - Configurable sync settings

5. **Error Handling**
   - Token expiration detection and refresh
   - Detailed error messages
   - Retry logic with exponential backoff
   - Admin monitoring and resync tools

## Architecture

### Backend Components

#### Models (`oauth_models.py`)

**OAuthConnection**
- Stores OAuth credentials (encrypted at rest)
- Tracks sync state (cursor/token for incremental sync)
- Manages connection status (active, expired, revoked, error)
- Firm-scoped for multi-tenant isolation

**OAuthAuthorizationCode**
- Temporary storage for OAuth authorization flow
- CSRF protection via state token
- Automatic expiration (10 minutes)

#### Services

**GoogleCalendarService** (`google_service.py`)
- OAuth flow management
- Google Calendar API v3 integration
- Event CRUD operations
- Incremental sync with sync tokens

**MicrosoftCalendarService** (`microsoft_service.py`)
- OAuth flow management
- Microsoft Graph API integration
- Event CRUD operations
- Delta sync with delta links

**CalendarSyncService** (`sync_service.py`)
- Orchestrates bi-directional sync
- Handles both providers uniformly
- Implements conflict resolution
- Token refresh management
- Error handling and retry logic

#### API Endpoints (`oauth_views.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/calendar/oauth-connections/` | GET | List user's connections |
| `/api/calendar/oauth-connections/initiate_google_oauth/` | POST | Start Google OAuth |
| `/api/calendar/oauth-connections/initiate_microsoft_oauth/` | POST | Start Microsoft OAuth |
| `/api/calendar/oauth-connections/oauth_callback/` | POST/GET | OAuth callback handler |
| `/api/calendar/oauth-connections/{id}/disconnect/` | POST | Revoke connection |
| `/api/calendar/oauth-connections/{id}/sync_now/` | POST | Trigger manual sync |
| `/api/calendar/oauth-connections/{id}/sync_status/` | GET | Get sync status |
| `/api/calendar/oauth-connections/{id}/` | PATCH | Update settings |

### Frontend Components

#### Pages

**CalendarSync** (`pages/CalendarSync.tsx`)
- Main calendar sync management page
- Connection cards with status indicators
- OAuth initiation buttons
- Sync configuration form
- Manual sync trigger

**CalendarOAuthCallback** (`pages/CalendarOAuthCallback.tsx`)
- OAuth callback handler
- Success/error feedback
- Automatic redirect to settings

#### API Client (`api/calendar.ts`)
- TypeScript types for calendar data
- API wrapper functions
- Error handling

## User Guide

### Connecting a Calendar

1. Navigate to **Delivery > Calendar Sync** in the main menu
2. Click **Connect Google Calendar** or **Connect Microsoft Outlook**
3. Authorize ConsultantPro to access your calendar
4. You'll be redirected back to the Calendar Sync page
5. Your calendar will appear in the "Connected Calendars" section

### Configuring Sync Settings

1. Find your connected calendar in the list
2. Click **⚙️ Settings**
3. Configure:
   - **Enable Automatic Sync**: Toggle background sync on/off
   - **Sync Window**: Number of days to sync (7-365)
4. Click **Save**

### Manual Sync

1. Find your connected calendar
2. Click **🔄 Sync Now**
3. Wait for sync to complete
4. A popup will show the number of events pulled/pushed

### Disconnecting a Calendar

1. Find your connected calendar
2. Click **Disconnect**
3. Confirm the action
4. The connection will be revoked

## Technical Details

### OAuth Flow

#### Google Calendar

1. User clicks "Connect Google Calendar"
2. Backend creates `OAuthAuthorizationCode` record with state token
3. User redirects to Google OAuth consent screen
4. User authorizes ConsultantPro
5. Google redirects to callback with authorization code
6. Backend exchanges code for access/refresh tokens
7. Tokens stored in `OAuthConnection` (encrypted)
8. Connection status set to "active"

#### Microsoft Outlook

Same flow as Google, using Microsoft OAuth endpoints.

### Sync Process

**Pull (External → Internal)**

1. Call provider's events API with sync cursor/token
2. Parse external event data
3. Check for existing appointment by `external_event_id`
4. If exists: apply conflict resolution
5. If not exists: create new appointment
6. Update sync cursor for next incremental sync

**Push (Internal → External)**

1. Query appointments without `external_event_id`
2. Within sync window (default: ±30 days)
3. Belonging to connection's user
4. Status: confirmed
5. Create event in external calendar
6. Store `external_event_id` in appointment

**Conflict Resolution**

- Compare `updated_at` timestamps
- Most recently modified version wins
- Preserves intentional changes from either side

### Security

**Multi-Tenant Isolation**
- All queries are firm-scoped
- Users can only see their own connections
- Firm boundary enforced at model and view level

**Token Security**
- OAuth tokens encrypted at rest
- Automatic token refresh before expiration
- Secure state token for CSRF protection

**API Security**
- Staff-only access (`IsStaffUser` permission)
- Token-based authentication
- Rate limiting (configured in Django)

### Error Handling

**Token Expiration**
- Detected before sync attempt
- Automatic refresh using refresh token
- Connection status updated if refresh fails

**Sync Failures**
- Logged to `error_message` field
- Connection status set to "error"
- Retry logic with exponential backoff
- Admin tools for manual resync

**Provider Errors**
- Rate limiting handled gracefully
- Invalid token detection
- Network error retry

## Environment Variables

Required environment variables for calendar sync:

```bash
# Google Calendar
GOOGLE_CALENDAR_CLIENT_ID=your_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=your_client_secret
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:8000/api/calendar/oauth/callback/

# Microsoft Calendar
MICROSOFT_CALENDAR_CLIENT_ID=your_client_id
MICROSOFT_CALENDAR_CLIENT_SECRET=your_client_secret
MICROSOFT_CALENDAR_REDIRECT_URI=http://localhost:8000/api/calendar/oauth/callback/
```

### Setting Up OAuth Credentials

**Google Calendar:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google Calendar API"
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI
6. Copy client ID and secret

**Microsoft Outlook:**
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register a new application in Azure AD
3. Add Calendar.ReadWrite permissions
4. Create client secret
5. Add redirect URI
6. Copy client ID and secret

## Database Schema

### OAuthConnection Table

```sql
CREATE TABLE calendar_oauth_connections (
    connection_id BIGSERIAL PRIMARY KEY,
    firm_id BIGINT NOT NULL REFERENCES firms(firm_id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    provider VARCHAR(20) NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    scopes JSONB DEFAULT '[]',
    provider_user_id VARCHAR(255),
    provider_email VARCHAR(254),
    provider_metadata JSONB DEFAULT '{}',
    sync_enabled BOOLEAN DEFAULT true,
    sync_window_days INTEGER DEFAULT 30,
    last_sync_at TIMESTAMP,
    last_sync_cursor TEXT,
    status VARCHAR(20) DEFAULT 'active',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(firm_id, user_id, provider)
);

CREATE INDEX idx_oauth_conn_firm_user_provider ON calendar_oauth_connections(firm_id, user_id, provider);
CREATE INDEX idx_oauth_conn_firm_status ON calendar_oauth_connections(firm_id, status);
CREATE INDEX idx_oauth_conn_provider_status ON calendar_oauth_connections(provider, status);
```

### OAuthAuthorizationCode Table

```sql
CREATE TABLE calendar_oauth_authorization_codes (
    code_id BIGSERIAL PRIMARY KEY,
    state_token UUID UNIQUE NOT NULL,
    firm_id BIGINT NOT NULL REFERENCES firms(firm_id),
    user_id BIGINT NOT NULL REFERENCES users(id),
    provider VARCHAR(20) NOT NULL,
    authorization_code TEXT,
    redirect_uri VARCHAR(512) NOT NULL,
    state VARCHAR(20) DEFAULT 'pending',
    expires_at TIMESTAMP NOT NULL,
    connection_id BIGINT REFERENCES calendar_oauth_connections(connection_id),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exchanged_at TIMESTAMP
);

CREATE INDEX idx_oauth_code_state_token ON calendar_oauth_authorization_codes(state_token);
CREATE INDEX idx_oauth_code_firm_user_state ON calendar_oauth_authorization_codes(firm_id, user_id, state);
CREATE INDEX idx_oauth_code_expires_at ON calendar_oauth_authorization_codes(expires_at);
```

## Testing

### Backend Tests

Calendar sync tests are located in:
- `src/modules/calendar/tests.py`
- `src/modules/calendar/test_workflow_execution.py`

Run tests:
```bash
cd src
pytest modules/calendar/
```

### Manual Testing

**Google Calendar Sync:**
1. Configure Google OAuth credentials
2. Connect Google Calendar via UI
3. Create appointment in ConsultantPro
4. Click "Sync Now"
5. Verify event appears in Google Calendar
6. Create event in Google Calendar
7. Click "Sync Now"
8. Verify appointment appears in ConsultantPro

**Microsoft Outlook Sync:**
1. Configure Microsoft OAuth credentials
2. Connect Microsoft Outlook via UI
3. Follow same steps as Google Calendar test

## Performance Considerations

**Incremental Sync**
- Google: Uses `syncToken` for delta queries
- Microsoft: Uses `deltaLink` for delta queries
- Reduces API calls and data transfer
- Faster sync times after initial sync

**Sync Window**
- Default: 30 days (past and future)
- Configurable per connection
- Smaller windows = faster syncs
- Recommended: 30-90 days

**Background Sync**
- Scheduled via Celery (if configured)
- Runs periodically for all active connections
- Respects rate limits
- Graceful degradation on failures

## Troubleshooting

### Connection Status: Expired

**Problem:** Access token has expired

**Solution:**
1. System will attempt automatic refresh
2. If refresh fails, reconnect calendar
3. Check OAuth credentials are valid

### Sync Fails with Error

**Problem:** Sync returns error message

**Solution:**
1. Check error message in connection card
2. Common causes:
   - Rate limiting: Wait and retry
   - Invalid token: Reconnect calendar
   - Network error: Check connectivity
3. Try manual sync
4. Contact admin if persists

### Events Not Syncing

**Problem:** Events not appearing after sync

**Solution:**
1. Check sync window includes event dates
2. Verify event meets sync criteria (status: confirmed)
3. Check for conflicts (last-modified-wins)
4. Review error messages
5. Try disconnecting and reconnecting

## Future Enhancements

Potential improvements for future sprints:

1. **Apple Calendar (iCloud) Support**
   - Add Apple OAuth provider
   - Implement CalDAV protocol

2. **Two-Way Update Sync**
   - Currently: Create-only sync
   - Future: Update existing events when modified

3. **Delete Sync**
   - Propagate deletions between systems
   - Configurable: keep or delete

4. **Selective Sync**
   - Choose which calendars to sync
   - Filter by calendar color/category
   - Exclude specific event types

5. **Real-Time Sync**
   - Webhook support for instant updates
   - Push notifications instead of polling

6. **Conflict Resolution Options**
   - User-configurable strategy
   - Manual conflict resolution UI
   - Three-way merge

7. **Bulk Operations**
   - Import historical events
   - Export all appointments
   - Batch disconnect/reconnect

8. **Analytics**
   - Sync success rate metrics
   - Performance monitoring
   - Usage statistics

## Support

For issues or questions:
- Check error messages in connection card
- Review logs: `src/logs/`
- Contact platform admin for OAuth credential issues
- File bug reports via GitHub Issues

## References

- [Google Calendar API Documentation](https://developers.google.com/calendar)
- [Microsoft Graph Calendar API](https://docs.microsoft.com/en-us/graph/api/resources/calendar)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [ConsultantPro Architecture Overview](../docs/04-explanation/architecture-overview.md)
