from custom_components.whatsapp.api import WhatsAppApiClient


def test_jid_normalization():
    """Test JID normalization logic."""
    client = WhatsAppApiClient(host="http://localhost:8066")

    # Phone numbers
    assert client.ensure_jid("49123456789") == "49123456789@s.whatsapp.net"
    assert client.ensure_jid("+49123456789") == "49123456789@s.whatsapp.net"
    assert client.ensure_jid("  49123456789  ") == "49123456789@s.whatsapp.net"
    assert client.ensure_jid("0151 12345678") == "015112345678@s.whatsapp.net"

    # Groups
    assert client.ensure_jid("12345-6789") == "12345-6789@g.us"
    assert client.ensure_jid("12345-6789@g.us") == "12345-6789@g.us"

    # Full JIDs
    full_jid = "49123456789@s.whatsapp.net"
    assert client.ensure_jid(full_jid) == full_jid
    assert client.ensure_jid("something@lid") == "something@lid"

    # Empty
    assert client.ensure_jid("") == ""
    assert client.ensure_jid(None) is None
