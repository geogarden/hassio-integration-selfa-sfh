"""Config flow for Selfa SFH Hybrid Inverter."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    DEFAULT_PORT,
    DEFAULT_SLAVE_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_PROTOCOL,
    PROTOCOLS,
    CONF_SLAVE_ID,
    CONF_PROTOCOL,
)
from .modbus_client import SelfahybridModbusClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_SLAVE_ID, default=DEFAULT_SLAVE_ID): vol.All(int, vol.Range(min=1, max=247)),
        vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(PROTOCOLS),
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            int, vol.Range(min=5, max=3600)
        ),
    }
)


class SelfahybridConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Selfa SFH."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            slave_id = user_input[CONF_SLAVE_ID]
            protocol = user_input[CONF_PROTOCOL]

            # Attempt connection test
            client = SelfahybridModbusClient(host, port, slave_id, protocol)
            connected = await client.connect()
            if connected:
                test = await client.read_registers(0x000B, 1)
                await client.disconnect()
                if test is None:
                    errors["base"] = "cannot_read"
                else:
                    await self.async_set_unique_id(f"selfa_sfh_{host}_{port}_{slave_id}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Selfa SFH ({host})",
                        data=user_input,
                    )
            else:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
