"""FreeCAD Bot Output Helper Module.

Copyright (c) 2025 Asymworks, LLC.
All Rights Reserved.
"""

import json

from typing import Optional

from fcbot.config import FCBotConfigOutput

from .base import OutputRunner
from .pdf import PdfOutputRunner
from .screenshot import ScreenshotOutputRunner
from .shape import StepOutputRunner, StlOutputRunner

#: Mapping of `type` parameter to `OutputRunner` subclass
OUTPUT_CLASSES = {
    'pdf':  PdfOutputRunner,
    'step': StepOutputRunner,
    'stl':  StlOutputRunner,
    'screenshot': ScreenshotOutputRunner,
}

def load_runner(
    config: FCBotConfigOutput,
    default_name: str,
    *,
    base_dir: Optional[str] = None
) -> OutputRunner:
    """Load an Output Runner from a configuration block."""
    if not config.name:
        config.name = default_name

    if not config.output_type:
        raise ValueError(f'Output {config.name} must have "type" key set to a string')
    
    output_cls = OUTPUT_CLASSES.get(config.output_type.lower())
    if not output_cls:
        raise KeyError(f'Output Type "{config.output_type}" is not supported')

    return output_cls(config, base_dir=base_dir)

def load_runner_json(
    config_json: str,
    default_name: str,
    *,
    base_dir: Optional[str]
) -> OutputRunner:
    """Load an Output Runner from a JSON configuration block."""
    config = FCBotConfigOutput.model_validate_json(config_json)
    return load_runner(config, default_name, base_dir=base_dir)
