"""Binary sensor for HA WhatsApp."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import WhatsAppApiClient
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WhatsApp binary sensors."""
    client: WhatsAppApiClient = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([WhatsAppConnectionSensor(client, entry)])


class WhatsAppConnectionSensor(BinarySensorEntity):  # type: ignore[misc]
    """Representation of a WhatsApp connection status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = None  # Use device name + device class

    def __init__(self, client: WhatsAppApiClient, entry: ConfigEntry) -> None:
        """Initialize."""
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_connection"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
            "manufacturer": "HA WhatsApp",
            "model": "API Client",
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (connected)."""
        # In a real implementation, this would likely use a Coordinator to
        # poll or push updates.
        # For this scaffold, we check the client state directly
        # (synchronously assumed for property).
        # We need to make sure the client exposes a way to check this without
        # async for this property
        # OR better: use a DataUpdateCoordinator.
        # For simplicity in this scaffold without a full Coordinator, we assume
        # a connected property.

        # NOTE: self.client.is_connected is async in our API definition.
        # Ideally we use a coordinator. Let's patch 'is_on' to return the
        # internal state variable.
        return self.client._connected
