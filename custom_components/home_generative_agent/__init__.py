"""Home Generative Agent Azure Initalization."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.const import CONF_API_KEY, CONF_URL, CONF_API_VERSION, CONF_MODEL, Platform
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.httpx_client import get_async_client
from langchain_core.runnables import ConfigurableField
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_openai import ChatOpenAI, AzureChatOpenAI

from .const import (
    EMBEDDING_MODEL_URL,
    RECOMMENDED_EMBEDDING_MODEL,
    RECOMMENDED_VLM,
    VLM_URL,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = (Platform.CONVERSATION,)

type HGAConfigEntry = ConfigEntry[HGAData]

@dataclass
class HGAData:
    """Data for Home Generative Assistant."""

    # chat_model: ChatOpenAIs
    chat_model: AzureChatOpenAI
    vision_model: ChatOllama

async def async_setup_entry(hass: HomeAssistant, entry: HGAConfigEntry) -> bool:
    """Set up Home generative Agent from a config entry."""
    # chat_model = ChatOpenAI( #TODO: fix blocking call
    #     api_key=entry.data.get(CONF_API_KEY),
    #     openai_api_base=entry.data.get(CONF_URL),
    #     timeout=10,
    #     http_async_client=get_async_client(hass),
    # ).configurable_fields(
    #     model_name=ConfigurableField(id="model_name"),
    #     temperature=ConfigurableField(id="temperature"),
    #     top_p=ConfigurableField(id="top_p"),
    # )
    chat_model = AzureChatOpenAI( #TODO: fix blocking call
        azure_endpoint=entry.data.get(CONF_URL),
        api_key=entry.data.get(CONF_API_KEY),
        api_version=entry.data.get(CONF_API_VERSION),
        azure_deployment=entry.data.get(CONF_MODEL),
        model=entry.data.get(CONF_MODEL),
        timeout=10,
        http_async_client=get_async_client(hass),
    ).configurable_fields(
        temperature=ConfigurableField(id="temperature"),
        top_p=ConfigurableField(id="top_p"),
    )

    try:
        await hass.async_add_executor_job(chat_model.get_name)
    except HomeAssistantError as err:
        LOGGER.error("Error setting up ChatOpenAI: %s", err)
        return False

    entry.chat_model = chat_model

    vision_model = ChatOllama(
        model=RECOMMENDED_VLM,
        base_url=VLM_URL,
        http_async_client=get_async_client(hass)
    ).configurable_fields(
        model=ConfigurableField(id="model"),
        format=ConfigurableField(id="format"),
        temperature=ConfigurableField(id="temperature"),
        top_p=ConfigurableField(id="top_p"),
        num_predict=ConfigurableField(id="num_predict"),
    )

    try:
        await hass.async_add_executor_job(vision_model.get_name)
    except HomeAssistantError as err:
        LOGGER.error("Error setting up VLM: %s", err)
        return False

    entry.vision_model = vision_model

    embedding_model = OllamaEmbeddings(
        model=RECOMMENDED_EMBEDDING_MODEL,
        base_url=EMBEDDING_MODEL_URL
    )

    #try:
        #await hass.async_add_executor_job(embedding_model.get_name)
    #except HomeAssistantError as err:
        #LOGGER.error("Error setting up embedding model: %s", err)
        #return False

    entry.embedding_model = embedding_model

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Home Generative Agent."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
