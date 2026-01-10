from app.services.email_templates import EmailBranding, PasswordResetEmailTemplate, VerificationEmailTemplate


def test_verification_email_template_includes_logo_and_verification_url():
    branding = EmailBranding.parlay_gorilla("https://parlaygorilla.com")
    template = VerificationEmailTemplate(branding)

    verification_url = "https://parlaygorilla.com/auth/verify-email?token=abc123"
    rendered = template.render(user_name="Fawl3", verification_url=verification_url)

    assert rendered.subject.lower().startswith("verify your")
    # Logo should be present (either as URL or embedded data URI)
    assert branding.logo_src in rendered.html
    # If logo is embedded, it will be a data URI; otherwise it's the URL
    assert branding.logo_url in rendered.html or "data:image" in rendered.html
    assert verification_url in rendered.html
    assert verification_url in rendered.text


def test_verification_email_template_escapes_user_name_in_html():
    branding = EmailBranding.parlay_gorilla("https://parlaygorilla.com")
    template = VerificationEmailTemplate(branding)

    verification_url = "https://parlaygorilla.com/auth/verify-email?token=abc123"
    rendered = template.render(user_name="<b>bad</b>", verification_url=verification_url)

    assert "<b>bad</b>" not in rendered.html
    assert "&lt;b&gt;bad&lt;/b&gt;" in rendered.html


def test_password_reset_email_template_includes_logo_and_reset_url():
    branding = EmailBranding.parlay_gorilla("https://parlaygorilla.com")
    template = PasswordResetEmailTemplate(branding)

    reset_url = "https://parlaygorilla.com/auth/reset-password?token=abc123"
    rendered = template.render(user_name="Fawl3", reset_url=reset_url)

    assert rendered.subject.lower().startswith("reset your")
    # Logo should be present (either as URL or embedded data URI)
    assert branding.logo_src in rendered.html
    # If logo is embedded, it will be a data URI; otherwise it's the URL
    assert branding.logo_url in rendered.html or "data:image" in rendered.html
    assert reset_url in rendered.html
    assert reset_url in rendered.text


def test_email_branding_allows_logo_override():
    branding = EmailBranding.parlay_gorilla(
        "https://parlaygorilla.com",
        "https://cdn.parlaygorilla.com/assets/newlogo.png",
    )
    assert branding.logo_url == "https://cdn.parlaygorilla.com/assets/newlogo.png"


