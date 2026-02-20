"""Constants for the HA WhatsApp integration.

All configuration keys, domain identifiers, and default values used
across the integration are defined here to avoid magic strings in
multiple places.

Constants:
    DOMAIN: Unique integration domain used in ``hass.data`` and service
        registrations.
    CONF_API_KEY: Config-entry key for the addon API key.
    CONF_SESSION_ID: The unique session identifier for the WhatsApp instance.
    CONF_MASK_SENSITIVE_DATA: Whether to mask phone numbers in logs.
    CONF_DEBUG_PAYLOADS: Whether to log raw outgoing payloads for debugging.
    CONF_POLLING_INTERVAL: Options-entry key for the event-poll interval
        in seconds.
    DEFAULT_PORT: Default port on which the WhatsApp addon listens.
    CONF_URL: Config-entry key for the base URL of the addon REST API.
    CONF_MARK_AS_READ: Options-entry key that controls automatic
        ``mark-as-read`` behaviour for incoming messages.
    CONF_RETRY_ATTEMPTS: Options-entry key for the number of retry
        attempts on send failures.
    CONF_WHITELIST: Options-entry key for a comma-separated list of
        allowed phone numbers / JIDs.
    EVENT_MESSAGE_RECEIVED: Home Assistant event name fired whenever a
        new WhatsApp message is received.
"""

DOMAIN = "whatsapp"
CONF_API_KEY = "api_key"
CONF_POLLING_INTERVAL = "polling_interval"
DEFAULT_PORT = 8066
CONF_URL = "url"
CONF_MARK_AS_READ = "mark_as_read"
CONF_RETRY_ATTEMPTS = "retry_attempts"

CONF_WHITELIST = "whitelist"
CONF_SESSION_ID = "session_id"
CONF_MASK_SENSITIVE_DATA = "mask_sensitive_data"
CONF_DEBUG_PAYLOADS = "debug_payloads"
EVENT_MESSAGE_RECEIVED = "whatsapp_message_received"
