"""FreeCAD Shape Output Classes.

Copyright (c) 2025 Asymworks, LLC.
All Rights Reserved.
"""

import logging
import os
import shutil
import tempfile

from typing import Any, Optional

from .base import OutputRunner


class StepOutputRunner(OutputRunner):
    """Export STEP files from FreeCAD Shapes."""
    def __init__(self, config: dict[str, Any], *, base_dir: Optional[str] = None):
        super().__init__(config, base_dir=base_dir)

    def _checkItem(self, item: object) -> bool:
        """Check that the items implement `Part::PropertyPartShape`."""
        if not hasattr(item, 'supportedProperties'):
            logging.debug(f'<{self.name}> Object {item.Label} does not provide a supportedProperties method')
            return False

        if 'Part::PropertyPartShape' not in item.supportedProperties():
            logging.debug(f'<{self.name}> Object {item.Label} does not seem to be a Solid')
            return False

        return True

    def _execute(self, doc: 'App.Document', items: list[object]) -> None:
        """Export Shape objects to a STEP file."""
        import Import

        if not items:
            logging.warning(f'<{self.name}> Empty item list passed to _execute()')
            return

        abs_fn = self.checkOutputFile(self.filename)
        with tempfile.TemporaryDirectory() as export_dir:
            logging.debug(f'<{self.name}> Using temporary export directory {export_dir}')
            export_fn = os.path.join(export_dir, f'export.step')

            try:
                logging.info(f'<{self.name}> Exporting {len(items)} items as STEP to {abs_fn}')
                Import.export(items, export_fn)
                if not os.path.isfile(export_fn):
                    logging.error(f'<{self.name}> FreeCAD did not generate export file {export_fn}')
                    return

                logging.debug(f'<{self.name}> Renaming {export_fn} to {abs_fn}')
                shutil.copy(export_fn, abs_fn)
                os.unlink(export_fn)

            except Exception as e:
                logging.error(f'<{self.name}> Failed to export to STEP: {repr(e)}')


class StlOutputRunner(OutputRunner):
    """Export STL files from FreeCAD Shapes."""
    def __init__(self, config: dict[str, Any], *, base_dir: Optional[str] = None):
        super().__init__(config, base_dir=base_dir)

    def _checkItem(self, item: object) -> bool:
        """Check that the items provide a `Shape` property."""
        if not hasattr(item, 'Shape'):
            logging.debug(f'<{self.name}> Object {item.Label} does not have a Shape property')
            return False

        return True

    def _execute(self, doc: 'App.Document', items: list[object]) -> None:
        """Export Shape objects to a STL file."""
        if not items:
            logging.warning(f'<{self.name}> Empty item list passed to _execute()')
            return

        if len(items) > 1:
            logging.error(f'<{self.name}> Only one object may be output to STL at a time')
            return

        abs_fn = self.checkOutputFile(self.filename)
        with tempfile.TemporaryDirectory() as export_dir:
            logging.debug(f'<{self.name}> Using temporary export directory {export_dir}')
            export_fn = os.path.join(export_dir, f'export.stl')

            try:
                logging.info(f'<{self.name}> Exporting {len(items)} items as STL to {abs_fn}')
                items[0].Shape.exportStl(export_fn)
                if not os.path.isfile(export_fn):
                    logging.error(f'<{self.name}> FreeCAD did not generate export file {export_fn}')
                    return

                logging.debug(f'<{self.name}> Renaming {export_fn} to {abs_fn}')
                shutil.copy(export_fn, abs_fn)
                os.unlink(export_fn)

            except Exception as e:
                logging.error(f'<{self.name}> Failed to export to STL: {repr(e)}')
