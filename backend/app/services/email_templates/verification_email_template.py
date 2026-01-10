import html
from datetime import datetime, timezone

from .branding import EmailBranding
from .rendered_email import RenderedEmail


class VerificationEmailTemplate:
    """Parlay Gorilla themed email verification template."""

    def __init__(self, branding: EmailBranding):
        self._branding = branding

    def render(self, user_name: str, verification_url: str) -> RenderedEmail:
        display_name = self._sanitize_display_name(user_name)
        safe_name = html.escape(display_name, quote=True)
        safe_verify_url_attr = html.escape(verification_url or "", quote=True)

        year = datetime.now(timezone.utc).year

        subject = f"Verify your {self._branding.app_name} account"
        html_content = f"""\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="supported-color-schemes" content="dark">
  <style>
    :root {{ color-scheme: dark; supported-color-schemes: dark; }}
  </style>
  <title>{html.escape(subject, quote=True)}</title>
</head>
<body bgcolor="{self._branding.background}" style="margin:0;padding:0;background-color:{self._branding.background};color-scheme:dark;supported-color-schemes:dark;">
  <!-- Preheader (hidden) -->
  <div style="display:none;max-height:0;overflow:hidden;mso-hide:all;opacity:0;color:transparent;visibility:hidden;">
    Verify your email to unlock Parlay Gorilla.
  </div>

  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" bgcolor="{self._branding.background}" style="background-color:{self._branding.background};padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellspacing="0" cellpadding="0" bgcolor="#0b0b10" style="width:600px;max-width:600px;background-color:#0b0b10;border:1px solid rgba(0,255,140,0.25);border-radius:18px;overflow:hidden;box-shadow:0 0 28px rgba(0,255,140,0.12);">
          <!-- Header -->
          <tr>
            <td align="center" bgcolor="#07070b" style="padding:28px 32px 18px;background-color:#07070b;">
              <img src="{html.escape(self._branding.logo_src, quote=True)}" width="240" alt="{html.escape(self._branding.app_name, quote=True)}" style="display:block;width:240px;max-width:240px;height:auto;margin:0 auto;border:0;outline:none;text-decoration:none;-ms-interpolation-mode:bicubic;">
              <div style="margin-top:12px;font-size:13px;letter-spacing:0.12em;color:rgba(0,255,140,0.75);">
                AI PARLAY INTEL • BUILT FOR GRINDERS
              </div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:28px 32px 8px;">
              <h1 style="margin:0 0 10px;font-size:24px;line-height:1.25;color:#ffffff;font-weight:800;">
                Verify your email
              </h1>
              <p style="margin:0 0 16px;font-size:15px;line-height:1.7;color:#b6b6c4;">
                Hey {safe_name}, welcome to {html.escape(self._branding.app_name, quote=True)}.
                Confirm this email address to secure your account and start building smarter parlays.
              </p>
              <p style="margin:0 0 22px;font-size:15px;line-height:1.7;color:#b6b6c4;">
                This link expires in <strong style="color:#e7e7ef;">48 hours</strong>.
              </p>
            </td>
          </tr>

          <!-- CTA -->
          <tr>
            <td align="center" style="padding:0 32px 18px;">
              <a href="{safe_verify_url_attr}" style="display:inline-block;background-color:{self._branding.primary_neon};color:#020203;text-decoration:none;font-weight:800;font-size:15px;padding:14px 24px;border-radius:12px;border:1px solid rgba(0,255,140,0.35);">
                Verify email address
              </a>
              <div style="margin-top:14px;font-size:12px;line-height:1.5;color:rgba(182,182,196,0.75);">
                If the button doesn't work, copy this link:
              </div>
              <div style="margin-top:6px;font-size:12px;line-height:1.5;word-break:break-all;">
                <a href="{safe_verify_url_attr}" style="color:{self._branding.primary_neon};text-decoration:none;">
                  {html.escape(verification_url or "", quote=True)}
                </a>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:18px 32px 28px;border-top:1px solid rgba(255,255,255,0.08);">
              <p style="margin:0;font-size:12px;line-height:1.6;color:rgba(182,182,196,0.75);text-align:center;">
                If you didn't create an account, you can safely ignore this email.
              </p>
              <p style="margin:10px 0 0;font-size:12px;line-height:1.6;color:rgba(182,182,196,0.55);text-align:center;">
                © {year} {html.escape(self._branding.app_name, quote=True)}. All rights reserved.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

        text_content = (
            f"{self._branding.app_name} — Verify your email\n\n"
            f"Hey {display_name},\n\n"
            "Welcome! Verify your email address to secure your account:\n\n"
            f"{verification_url}\n\n"
            "This link expires in 48 hours.\n\n"
            "If you didn't create an account, you can safely ignore this email.\n\n"
            f"© {year} {self._branding.app_name}\n"
        )

        return RenderedEmail(subject=subject, html=html_content, text=text_content)

    @staticmethod
    def _sanitize_display_name(user_name: str) -> str:
        value = (user_name or "").strip()
        value = value.replace("\r", " ").replace("\n", " ").strip()
        return value or "there"


