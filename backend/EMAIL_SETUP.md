# Email Setup Guide

## Problem: Emails Not Being Sent

If you're not receiving verification or password reset emails, it's because the `RESEND_API_KEY` is not configured.

## Quick Setup

1. **Get a free Resend API key:**
   - Go to https://resend.com
   - Sign up for a free account (3000 emails/month free)
   - Navigate to API Keys section
   - Create a new API key

2. **Add to your `.env` file:**
   ```bash
   RESEND_API_KEY=re_your_api_key_here
   ```

3. **Restart your backend server:**
   ```bash
   # The server needs to be restarted to pick up the new environment variable
   ```

## Verification

After setting up, check your backend logs when requesting a password reset:
- ✅ **Success**: `Email sent successfully to user@example.com: Reset your Parlay Gorilla password`
- ❌ **Missing Key**: `⚠️ EMAIL NOT SENT: RESEND_API_KEY not configured`

## Email Types Sent

- **Email Verification**: Sent after user registration
- **Password Reset**: Sent when user requests password reset
- **Resend Verification**: Sent when user requests verification email again

## Development Mode

If `RESEND_API_KEY` is not set, the system will:
- Log a warning that email was not sent
- Still return success to the frontend (so flows continue)
- Allow you to test the UI without actually sending emails

**Note**: In production, you MUST configure `RESEND_API_KEY` for users to receive emails.

