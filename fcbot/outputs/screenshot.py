"""FreeCAD Screenshot Output Classes.

Copyright (c) 2025 Asymworks, LLC.
All Rights Reserved.
"""

import enum
import logging
import os
import shutil
import tempfile

from typing import Any, Optional, Union

from pydantic import BaseModel

from .base import OutputRunner

class FCCameraType(enum.Enum):
    """Defines the FreeCAD Camera Types used for Screenshots."""
    Orthographic = 'orthographic'
    Perspective = 'perspective'


class FCViewType(enum.Enum):
    """Defines the pre-defined FreeCAD View Types used for Screenshots."""
    Axometric = 'axometric'
    Axonometric = 'axonometric'
    Bottom = 'bottom'
    Dimetric = 'dimetric'
    Front = 'front'
    Isometric = 'isometric'
    Left = 'left'
    Rear = 'rear'
    Right = 'right'
    Top = 'top'
    Trimetric = 'trimetric'


class FCViewPosition(BaseModel):
    """Defines a custom FreeCAD Camera View."""
    x: float
    y: float
    z: float
    yaw: float
    pitch: float
    roll: float


class FCBotScreenshotOptions(BaseModel):
    """Options Schema for the `screenshot` output type."""
    camera: FCCameraType
    view: Union[FCViewType, FCViewPosition]
    resolution: tuple[int, int]
    background: str = 'transparent'


class ScreenshotOutputRunner(OutputRunner):
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
        import FreeCADGui

        if not items:
            logging.warning(f'<{self.name}> Empty item list passed to _execute()')
            return

        item_names = set([item.Name for item in items])
        item_visibility = dict()

        def restoreVisibility():
            for name, vis in item_visibility.items():
                try:
                    obj = doc.getObject(name)
                    if obj and hasattr(obj, 'Visibility'):
                        obj.Visibility = visibility
                except:
                    pass

        abs_fn = self.checkOutputFile(self.filename)
        ext = os.path.splitext(self.filename)[-1][1:]
        temp_fn = f'export.{ext}'
        with tempfile.TemporaryDirectory() as export_dir:
            logging.debug(f'<{self.name}> Using temporary export directory {export_dir}')
            export_fn = os.path.join(export_dir, temp_fn)

            try:
                logging.debug(f'<{self.name}> Hiding other objects from view')
                for obj in self.collectShapes(doc):
                    visibility = obj.Name in item_names
                    if visibility != obj.Visibility:
                        item_visibility[obj.Name] = obj.Visibility
                        obj.Visibility = visibility

                logging.debug(f'<{self.name}> Setting up new View3D')
                FreeCADGui.runCommand('Std_ViewCreate', 0)
                view = FreeCADGui.ActiveDocument.ActiveView
                if not view or not hasattr(view, 'saveImage'):
                    logging.error(f'<{self.name}> Std_ViewCreate did not create a Gui::View3DInventor')
                    restoreVisibility()
                    return

                logging.debug(f'<{self.name}> Calling view.setCameraType({self._options.camera.name})')
                view.setCameraType(self._options.camera.name)

                if isinstance(self._options.view, FCViewType):
                    viewMethod = f'view{self._options.view.name}'
                    if not hasattr(view, viewMethod):
                        logging.error(f'<{self.name}> {viewMethod} is not a recognized method on Gui::View3DInventor')
                        restoreVisibility()
                        return

                    logging.debug(f'<{self.name}> Calling view.{viewMethod}')
                    getattr(view, viewMethod)()

                else:
                    logging.error(f'<{self.name}> We do not know how to set arbitrary camera position yet')
                    restoreVisibility()
                    return

                res_x, res_y = self._options.resolution

                logging.info(f'<{self.name}> Capturing screenshot of {len(items)} items as {ext.upper()} to {abs_fn}')
                logging.debug(f'<{self.name}> Calling view.saveImage({export_fn}, {res_x}, {res_y}, {self._options.background})')
                view.fitAll()
                view.saveImage(export_fn, res_x, res_y, self._options.background)
                if not os.path.isfile(export_fn):
                    logging.error(f'<{self.name}> FreeCAD did not generate export file {export_fn}')
                    restoreVisibility()
                    return

                restoreVisibility()

                logging.debug(f'<{self.name}> Renaming {export_fn} to {abs_fn}')
                shutil.copy(export_fn, abs_fn)
                os.unlink(export_fn)

            except Exception as e:
                logging.error(f'<{self.name}> Failed to export screenshot: {repr(e)}')

    def _loadOptions(self, options: dict[str, Any]) -> Any:
        """Load Output-Type Specific Options."""
        return FCBotScreenshotOptions.model_validate(options)
