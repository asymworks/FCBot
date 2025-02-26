"""FreeCAD Bot Main Application.

Copyright (c) 2025 Asymworks, LLC.
All Rights Reserved.
"""

import argparse
import configparser
import logging
import os
import pathlib
import subprocess
import sys
import tempfile

import jinja2
import yaml

from dataclasses import asdict, field, dataclass
from typing import Tuple

from fcbot.config import load_config
from fcbot.outputs import OutputRunner, load_runner

__NAME__ = 'FCBot'
__PACKAGE__ = 'fcbot'
__VERSION__ = '0.1.0'


@dataclass
class Context:
    config_filename: str
    extra_sys_paths: list[str]
    input_filename: str
    logging_level: str
    output_dir: str | None
    outputs: list[OutputRunner]


def quote(input: str) -> str:
    """Jinja2 filter to quote a string."""
    return repr(str(input))


def main():
    """FCBot Main Entry Point."""
    parser = argparse.ArgumentParser(
        prog='fcbot',
        description='FreeCAD Automation Tool for CI/CD Workflows',
    )
    parser.add_argument(
        '-c', '--config', type=str, default=[ 'fcbot.yaml' ],
        help='FCBot Configuration File'
    )
    parser.add_argument(
        '-o', '--output', type=str, default=None,
        help='Output directory (default is $CWD or value in "fcbot.output_dir" configuration key)'
    )
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help='Increase Verbosity Level (default is WARNING)'
    )
    parser.add_argument(
        '-V', '--version', action='store_true',
        help='Print FCBot version number and exit'
    )
    parser.add_argument(
        'input', metavar='INPUT', nargs='?', type=str,
        help='FreeCAD Input File (FCStd File)'
    )

    args = parser.parse_args()
    if args.version:
        # If we are printing the version only
        print(f'{__NAME__} {__VERSION__}')
        sys.exit(0)

    else:
        # Ensure an input file was provided
        if not args.input:
            print('Error: missing FreeCAD input file')
            parser.print_usage()
            sys.exit(1)

    # Initialize Logging Subsystem
    log_level = logging.WARNING
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose >= 2:
        log_level = logging.DEBUG

    from .logging import init_logging
    logger = init_logging(log_level)
    logger.info('FCBot Started')

    # Load Package Directory
    package_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    logger.debug(f'FCBot Package found at {package_dir}')

    # Check for Virtual Environment (needed for custom packages)
    venv_dir = None
    if sys.prefix != sys.base_prefix:
        logger.debug(f'Virtual Environment found at {sys.prefix}')
        for path in sys.path:
            if os.path.commonpath([sys.prefix, path]) == sys.prefix and 'site-packages' in path:
                venv_dir = path

        logger.debug(f'Virtual Environment site-packages found at {venv_dir}')

    # Load Configuration File
    if not os.path.exists(args.config):
        logger.error(f'Configuration file {args.config} not found')
        sys.exit(1)

    config = load_config(args.config)
    if not config:
        sys.exit(2)

    # Patch the Output Directory.
    # TODO: This is really hacky and should really be handled differently
    if config.fcbot.output_dir is None and args.output is not None:
        config.fcbot.output_dir = args.output
    logging.debug(f'Using output directory {config.fcbot.output_dir}')

    # Check Logging Configuration
    if config.fcbot.log_level not in logging.getLevelNamesMapping():
        logger.error(f'Invalid value for "fcbot.log_level": {config.fcbot.log_level}')
        sys.exit(3)

    # Process Output Configurations
    if not config.outputs:
        logger.warning(f'No Outputs found in configuration file, exiting cleanly')
        sys.exit(0)

    outputs = []
    for i, cfg_output in enumerate(config.outputs):
        outputs.append(load_runner(cfg_output, f'outputs[{i}]'))

    # Assemble Jinja Template Context
    extra_sys_paths = [ package_dir ]
    if venv_dir:
        extra_sys_paths.append(venv_dir)
    if config.fcbot.paths:
        extra_sys_paths.extend(config.fcbot.paths)

    context = Context(
        config_filename=os.path.abspath(args.config),
        input_filename=os.path.abspath(args.input),
        logging_level=config.fcbot.log_level,
        extra_sys_paths=extra_sys_paths,
        output_dir=config.fcbot.output_dir,
        outputs=outputs,
    )

    # Render the Jinja Template
    env = jinja2.Environment(loader=jinja2.PackageLoader('fcbot'))
    env.filters['quote'] = quote

    tmpl = env.get_template('script.py.j2')
    script = tmpl.render(config=config, **asdict(context))

    # Write to a temp file and run FreeCAD
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as script_file:
        logging.debug(f'Writing script file to {script_file.name}')
        script_file.write(script)
        script_file.close()

        if not os.path.exists(script_file.name):
            logging.error(f'Script file {script_file.name} disappeared')
            sys.exit(4)

        if not os.stat(script_file.name).st_size:
            logging.error(f'Script file {script_file.name} is empty after writing')
            os.unlink(script_file.name)
            sys.exit(4)

        fc_cmd = [ config.fcbot.freecad_cmd ]
        if venv_dir:
            fc_cmd.extend([ '-P', venv_dir ])
        if config.fcbot.freecad_args:
            fc_cmd.extend(config.fcbot.freecad_args)

        fc_cmd.append(script_file.name)

        logging.info(f'Starting FreeCAD with "{ fc_cmd[0] }"')
        logging.debug(f'Full FreeCAD command: {" ".join(fc_cmd)}')
        subprocess.run(fc_cmd, timeout=60)

        logging.debug(f'Removing script file {script_file.name}')
        os.unlink(script_file.name)

    logging.info(f'FCBot Run Complete')
