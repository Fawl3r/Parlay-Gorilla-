"""
Email template rendering for transactional messages (verification, password reset, etc.).

Keep templates isolated from delivery (Resend) to enforce SRP and make testing easy.
"""

from .branding import EmailBranding
from .logo_embedder import EmailLogoEmbedder
from .rendered_email import RenderedEmail
from .verification_email_template import VerificationEmailTemplate
from .password_reset_email_template import PasswordResetEmailTemplate

__all__ = [
    "EmailBranding",
    "EmailLogoEmbedder",
    "RenderedEmail",
    "VerificationEmailTemplate",
    "PasswordResetEmailTemplate",
]


