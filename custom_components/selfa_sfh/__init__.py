"""Selfa SFH integration: direct local Modbus gateway access."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_PROTOCOL,
    CONF_REQUEST_DELAY,
    CONF_SLAVE_ID,
    CONF_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_REQUEST_DELAY,
    DEFAULT_SLAVE_ID,
    DEFAULT_TIMEOUT,
)
from .coordinator import SelfahybridCoordinator
from .frontend import async_register_cards
from .modbus_client import SelfahybridModbusClient
from .registers import load_registers

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.BINARY_SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one client and one coordinator for all platforms."""
    options = {**entry.data, **entry.options}
    client = SelfahybridModbusClient(
        options[CONF_HOST],
        options.get(CONF_PORT, DEFAULT_PORT),
        options.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID),
        options.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
        timeout=options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        request_delay=options.get(CONF_REQUEST_DELAY, DEFAULT_REQUEST_DELAY) / 1000,
    )
    registers = await hass.async_add_executor_job(load_registers)
    coordinator = SelfahybridCoordinator(hass, entry, client, registers)
    try:
        await coordinator.async_config_entry_first_refresh()
        entry.runtime_data = coordinator
        await async_register_cards(hass)
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        await client.disconnect()
        raise
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    await entry.runtime_data.client.disconnect()
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Retain old gateway settings; new register keys keep measurement unique IDs."""
    if entry.version > 2:
        return False
    if entry.version == 1:
        hass.config_entries.async_update_entry(entry, version=2)
    return True
