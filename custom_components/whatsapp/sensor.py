"""Sensor platform for WhatsApp."""

from __future__ import annotations



from homeassistant.components.sensor import SensorEntity, SensorStateClass
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
    """Set up WhatsApp sensors."""
    client: WhatsAppApiClient = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        WhatsAppStatSensor(client, entry, "sent", "Messages Sent"),
        WhatsAppStatSensor(client, entry, "failed", "Messages Failed"),
    ])


class WhatsAppStatSensor(SensorEntity):  # type: ignore[misc]
    """Representation of a WhatsApp statistic sensor."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(
        self,
        client: WhatsAppApiClient,
        entry: ConfigEntry,
        stat_key: str,
        name: str
    ) -> None:
        """Initialize the sensor."""
        self.client = client
        self._stat_key = stat_key
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{stat_key}"
        self._attr_entity_registry_enabled_default = False
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "WhatsApp",
        }

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return int(self.client.stats.get(self._stat_key, 0))
