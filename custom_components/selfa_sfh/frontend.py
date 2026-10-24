"""Automatically serve the bundled Selfa dashboard card, as Wanas does."""

from pathlib import Path

from homeassistant.loader import async_get_integration

from .const import DOMAIN


async def async_register_cards(hass):
    key = f"{DOMAIN}_cards_registered"
    if hass.data.get(key) or hass.http is None or "frontend" not in hass.config.components:
        return
    from homeassistant.components.frontend import add_extra_js_url
    from homeassistant.components.http import StaticPathConfig

    path = Path(__file__).parent / "www" / "selfa-card.js"
    url = f"/{DOMAIN}_static/selfa-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(url, str(path), cache_headers=False)]
    )
    integration = await async_get_integration(hass, DOMAIN)
    add_extra_js_url(hass, f"{url}?v={integration.version}")
    hass.data[key] = True
