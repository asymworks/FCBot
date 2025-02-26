"""FreeCAD Bot Configuration Loader.

Copyright (c) 2025 Asymworks, LLC.
All Rights Reserved.
"""

import logging
import os

import yaml

from pydantic import BaseModel, Field
from typing import Any, Optional, Literal, Union


class FCBotConfigMeta(BaseModel):
    """Schema for FCBot Metadata Configuration."""
    freecad_cmd: str = 'freecad'
    freecad_args: Optional[list[str]] = None
    output_dir: Optional[str] = None
    log_level: str = 'INFO'
    paths: Optional[list[str]] = None
    version: Optional[int] = None


class FCBotAllPages(BaseModel):
    """Schema for FCBot "All Pages" Source."""
    pages: Literal['all']


class FCBotAllShapes(BaseModel):
    """Schema for FCBot "All Shapes" Source."""
    shapes: Literal['all']


class FCBotConfigOutput(BaseModel):
    """Schema for FCBot Output Configuration.
    
    `type`: Specifies the output type (e.g. `step`, `stl`, or `pdf`)
    `filename`: Specifies the output filename, relative to the output directory
    `objects`: Either a list of FreeCAD Object Labels or a `FCBotConfigSources`
    `name`: Short name for this output step, used in logging messages. Defaults
            to `output[x]` where `x` is the index of this `FCBotConfigOutput`
            in the list.
    `comment`: Longer comment for this output step, logged once prior to running
               the output step.
    `options`: Extra options specific to the output type.
    """
    output_type: str = Field(alias='type')
    filename: str
    objects: Union[
        list[str],
        FCBotAllPages,
        FCBotAllShapes,
    ]
    name: Optional[str] = None
    comment: Optional[str] = None
    options: Optional[dict[str, Any]] = None


class FCBotConfig(BaseModel):
    """Schema for FCBot Configuration."""
    fcbot: Optional[FCBotConfigMeta] = None
    outputs: Optional[list[FCBotConfigOutput]] = None


def load_config(filename: str) -> FCBotConfig | None:
    """Load FCBot Configuration from a YAML File."""
    with open(filename, 'r') as f:
        try:
            logging.debug(f'Loading configuration from {filename}')
            config_data = yaml.load(f, yaml.Loader)

        except Exception as exc:
            logging.error(f'Failed to read configuration file: {exc}')
            return None

    # Check that the YAML file is an object
    if not isinstance(config_data, dict):
        logging.error(f'Configuration file must be a mapping')
        return None

    # Check Version
    version = 1
    if 'fcbot' not in config_data:
        logging.warning(f'Missing "fcbot" key in configuration file, assuming configuration version 1')
    elif 'version' not in config_data['fcbot']:
        logging.warning(f'Missing "fcbot.version" key in configuration file, assuming version 1')
    else:
        version = config_data['fcbot']['version']

    if version != 1:
        logging.error(f'Configuration version {version} is not supported')
        return None

    # Check Schema with Pydantic
    return FCBotConfig.model_validate(config_data)
