from dataclasses import dataclass


@dataclass(frozen=True)
class RenderedEmail:
    """Rendered email content ready for delivery via provider."""

    subject: str
    html: str
    text: str


