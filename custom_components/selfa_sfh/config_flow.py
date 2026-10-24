"""UI configuration, connection testing, reconfiguration and polling options."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import callback

from .const import (
    CONF_PROTOCOL,
    CONF_REQUEST_DELAY,
    CONF_SETTINGS_INTERVAL,
    CONF_SLAVE_ID,
    CONF_TIMEOUT,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEFAULT_REQUEST_DELAY,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SETTINGS_INTERVAL,
    DEFAULT_SLAVE_ID,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PROTOCOLS,
)
from .modbus_client import (
    SelfaConnectionError,
    SelfahybridModbusClient,
    SelfaRegisterError,
)


def connection_schema(current: dict | None = None) -> vol.Schema:
    """Keep connection details separate from optional polling settings."""
    data = current or {}
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=data.get(CONF_HOST, "")): vol.All(
                str, vol.Length(min=1)
            ),
            vol.Required(CONF_PORT, default=data.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                int, vol.Range(min=1, max=65535)
            ),
            vol.Required(CONF_SLAVE_ID, default=data.get(CONF_SLAVE_ID, DEFAULT_SLAVE_ID)): vol.All(
                int, vol.Range(min=1, max=247)
            ),
            vol.Required(CONF_PROTOCOL, default=data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)): vol.In(
                PROTOCOLS
            ),
        }
    )


async def validate_connection(data: dict) -> str | None:
    """Verify two documented registers. Read SN for a stable device identity."""
    client = SelfahybridModbusClient(
        data[CONF_HOST], data[CONF_PORT], data[CONF_SLAVE_ID], data[CONF_PROTOCOL]
    )
    try:
        await client.read_registers(10008, 1)
        await client.read_registers(10105, 1)
        try:
            serial_words = await client.read_registers(10000, 8)
        except SelfaRegisterError:
            return None
        raw = b"".join(word.to_bytes(2, "big") for word in serial_words).rstrip(b"\x00\xff ")
        if len(raw) >= 4 and all(32 <= byte < 127 for byte in raw) and set(raw) not in ({48}, {70}):
            return raw.decode("ascii")
        return None
    finally:
        await client.disconnect()


class SelfahybridConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure direct gateway access; no ESPHome node is involved."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SelfaOptionsFlow()

    async def _step_connection(self, step_id: str, user_input: dict | None = None):
        entry = self._get_reconfigure_entry() if step_id == "reconfigure" else None
        errors = {}
        if user_input is not None:
            user_input = {**user_input, CONF_HOST: user_input[CONF_HOST].strip()}
            for existing in self._async_current_entries():
                if entry and existing.entry_id == entry.entry_id:
                    continue
                if all(
                    existing.data.get(key) == user_input[key]
                    for key in (CONF_HOST, CONF_PORT, CONF_SLAVE_ID)
                ):
                    return self.async_abort(reason="already_configured")
            try:
                serial = await validate_connection(user_input)
            except SelfaConnectionError:
                errors["base"] = "cannot_connect"
            except SelfaRegisterError:
                errors["base"] = "cannot_read"
            else:
                if entry:
                    if entry.data.get("serial_number") and serial != entry.data["serial_number"]:
                        errors["base"] = "wrong_device"
                    else:
                        return self.async_update_reload_and_abort(
                            entry, data_updates={**user_input, "serial_number": serial}
                        )
                else:
                    if serial:
                        await self.async_set_unique_id(serial)
                        self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"Selfa SFH ({user_input[CONF_HOST]})",
                        data={**user_input, "serial_number": serial},
                    )
        return self.async_show_form(
            step_id=step_id,
            data_schema=connection_schema(user_input or (entry.data if entry else None)),
            errors=errors,
        )

    async def async_step_user(self, user_input=None):
        return await self._step_connection("user", user_input)

    async def async_step_reconfigure(self, user_input=None):
        return await self._step_connection("reconfigure", user_input)


class SelfaOptionsFlow(config_entries.OptionsFlow):
    """Configure intervals, request pacing and timeouts without YAML."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        data = {**self.config_entry.data, **self.config_entry.options}
        fields = {
            CONF_SCAN_INTERVAL: (DEFAULT_SCAN_INTERVAL, 15, 3600),
            CONF_SETTINGS_INTERVAL: (DEFAULT_SETTINGS_INTERVAL, 60, 86400),
            CONF_REQUEST_DELAY: (DEFAULT_REQUEST_DELAY, 0, 2000),
            CONF_TIMEOUT: (DEFAULT_TIMEOUT, 1, 30),
        }
        schema = vol.Schema(
            {
                vol.Required(key, default=data.get(key, default)): vol.All(
                    int, vol.Range(min=low, max=high)
                )
                for key, (default, low, high) in fields.items()
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
