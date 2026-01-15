from app.services.email_templates import EmailLogoEmbedder


def test_email_logo_embedder_encodes_small_logo(tmp_path):
    logo_path = tmp_path / "logo.png"
    logo_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 128)

    embedder = EmailLogoEmbedder(max_inline_bytes=1024)
    data_uri = embedder.embed_logo_as_data_uri(logo_path)

    assert data_uri is not None
    assert data_uri.startswith("data:image/png;base64,")


def test_email_logo_embedder_skips_large_logo(tmp_path):
    logo_path = tmp_path / "logo.png"
    logo_path.write_bytes(b"0" * 2048)

    embedder = EmailLogoEmbedder(max_inline_bytes=1024)
    data_uri = embedder.embed_logo_as_data_uri(logo_path)

    assert data_uri is None

