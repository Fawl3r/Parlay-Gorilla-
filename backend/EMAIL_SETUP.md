# Email Setup Guide

## Problem: Emails Not Being Sent

If you're not receiving verification or password reset emails, it's usually one of these:

- **Missing API key**: `RESEND_API_KEY` is not configured.
- **Resend test mode limitation**: Using `onboarding@resend.dev` only allows sending to your account owner email. To send to any email, you must verify a domain.
- **Sender not verified**: you're trying to send from `noreply@yourdomain.com` but the domain isn't verified in Resend.

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

3. **Set a valid sender (FROM) address:**

   ⚠️ **IMPORTANT**: Using `onboarding@resend.dev` only allows sending to your Resend account owner email (for testing). To send to any email address, you MUST verify a domain.

   **Option A: Test Mode (Limited)**
   ```bash
   RESEND_FROM="Parlay Gorilla <onboarding@resend.dev>"
   ```
   - ✅ Works for testing with your own email
   - ❌ Cannot send to other email addresses
   - ❌ Will get 403 error when sending to other emails

   **Option B: Production (Required for real users)**
   1. Go to https://resend.com/domains
   2. Add and verify your domain (e.g., `parlaygorilla.com`)
   3. Add DNS records (SPF, DKIM, DMARC) as instructed
   4. Wait for verification (usually a few minutes)
   5. Update your `.env`:
   ```bash
   RESEND_FROM="Parlay Gorilla <noreply@parlaygorilla.com>"
   ```
   - ✅ Can send to any email address
   - ✅ Better deliverability
   - ✅ Branded sender address

4. **Restart your backend server:**
   ```bash
   # The server needs to be restarted to pick up the new environment variable
   ```

## Verification

After setting up, check your backend logs when requesting a password reset:
- ✅ **Success**: `Email sent successfully to user@example.com: Reset your Parlay Gorilla password`
- ❌ **Missing Key**: `⚠️ EMAIL NOT SENT: RESEND_API_KEY not configured`
- ❌ **403 Error**: `Failed to send email via Resend: 403` - This means you're using test mode and trying to send to an email that's not your account owner email. Verify a domain to send to any email.

## Testing Email Sending

Run the test script to verify email configuration:

```bash
cd backend
python scripts/test_email_sending.py your@email.com
```

**Note**: If using `onboarding@resend.dev`, replace `your@email.com` with your Resend account owner email (the email you signed up with).

## Email Types Sent

- **Email Verification**: Sent after user registration
- **Password Reset**: Sent when user requests password reset
- **Resend Verification**: Sent when user requests verification email again

## Important: Links + Logos Must Be Publicly Reachable

Verification and password reset emails build links (and the logo image URL) using `APP_URL`.

- If `APP_URL` is `http://localhost:3000`, **your phone / other devices cannot reach it**, so:
  - The **Verify** link won’t open correctly
  - The **logo will not load** (you’ll see a broken image icon)
- For real-device testing, set `APP_URL` to a **public HTTPS URL** (your real domain, or your tunnel URL).

Optional:
- Set `EMAIL_LOGO_URL` to force a specific public logo URL in emails.

## Development Mode

If `RESEND_API_KEY` is not set, the system will:
- Log a warning that email was not sent
- Still allow signup/login flows to continue, but email endpoints will return an error
- Allow you to test the UI without actually sending emails

**Note**: In production, you MUST configure `RESEND_API_KEY` for users to receive emails.

