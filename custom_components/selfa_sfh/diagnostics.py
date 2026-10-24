"""Redacted connection details and register support information."""

from homeassistant.components.diagnostics import async_redact_data


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = entry.runtime_data
    return {
        "entry": async_redact_data(entry.as_dict(), {"host", "serial_number", "unique_id"}),
        "connected": coordinator.client._client is not None
        and coordinator.client._client.connected,
        "last_success": coordinator.last_success.isoformat() if coordinator.last_success else None,
        "unsupported": sorted(coordinator.unsupported),
        "register_count": len(coordinator.registers),
    }
