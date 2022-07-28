"""Config flow to configure the petsafe integration."""
import logging

import voluptuous as vol
from petsafe_scoopfree import PetSafeClient

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_ACCESS_TOKEN

_LOGGER = logging.getLogger(__name__)

from .const import (
    CONF_ID_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_ACCESS_TOKEN,
    DOMAIN,
    CODE,
    DATA_PETSAFE_CONFIG,
    ENABLE_PET,
)

class PetsafeFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a petsafe config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize the petsafe flow."""
        self._petsafe = None
        self._enable_pet = None

    async def async_step_user(self, user_input=None):
        """Create config entry. Show the setup form to the user."""
        if self._async_current_entries():
            # Config entry already exists, only one allowed.
            return self.async_abort(reason="single_instance_allowed")

        errors = {}
        stored_email = (
            self.hass.data[DATA_PETSAFE_CONFIG].get(CONF_EMAIL)
            if DATA_PETSAFE_CONFIG in self.hass.data
            else ""
        )
        if user_input is not None:
            # Use the user-supplied email to attempt to obtain a code from petsafe.
            self._petsafe = await self.hass.async_add_executor_job(
                PetSafeClient, user_input[CONF_EMAIL]
            )
            if await self.hass.async_add_executor_job(self._petsafe.request_code):
                # We have a code; move to the next step of the flow.
                return await self.async_step_authorize()
            errors["base"] = "pin_request_failed"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_EMAIL, default=stored_email): str}
            ),
            errors=errors,
        )

    async def async_step_authorize(self, user_input=None):
        """Present the user with the code so that the app can be authorized on petsafe."""
        errors = {}

        if user_input is not None:
            # Attempt to obtain tokens from petsafe and finish the flow.
            if await self.hass.async_add_executor_job(
                self._petsafe.request_tokens_from_code, user_input[CODE]
            ):
                # tokens obtained; create the config entry.
                config = {
                    CONF_EMAIL: self._petsafe.email,
                    CONF_REFRESH_TOKEN: self._petsafe.refresh_token,
                    CONF_ID_TOKEN: self._petsafe.id_token,
                    CONF_ACCESS_TOKEN: self._petsafe.access_token,
                    ENABLE_PET: self._enable_pet
                }
                return self.async_create_entry(title=DOMAIN, data=config)
            errors["base"] = "token_request_failed"

        return self.async_show_form(
            step_id="authorize",
            errors=errors,
            data_schema=vol.Schema({vol.Required(CODE): str}),
        )
