"""FreeCAD Output Helper Base Class.

Copyright (c) 2025 Asymworks, LLC.
All Rights Reserved.
"""

import json
import os
import logging

from typing import Any, Optional

from fcbot.config import FCBotAllPages, FCBotAllShapes, FCBotConfigOutput


class OutputRunner(object):
    """Base Class for FCBot Output Runners.

    This is an abstract base class for all FCBot output runners. Classes for
    specific output types must override `_loadOptions()` and `_execute()`.

    TODO: Passing `base_dir` to the constructor should probably be refactored
          to use a quasi-global object that holds other things from the `fcbot`
          configuration (and/or command line).
    """
    def __init__(self, config: dict[str, Any], *, base_dir: Optional[str] = None):
        self._base_dir = base_dir
        self._config = FCBotConfigOutput.model_validate(config)
        if self._config.options:
            self._options = self._loadOptions(self._config.options)

    def _checkItem(self, item: object) -> bool:
        """Check if an item can be exported by this runner.

        Subclasses should override this method. The default implementation
        always returns `True`.
        """
        return True

    def _execute(self, doc: 'App.Document', items: list[object]) -> None:
        """Run the actual output logic."""
        raise NotImplementedError()

    def _loadOptions(self, options: dict[str, Any]) -> Any:
        """Load Output-Type Specific Options."""
        pass

    def checkOutputFile(self, filename: str) -> str | None:
        """Check that an Output File should be writable.

        If the file is expected to be writable, its absolute path is returned. If
        the file will not be writable (i.e. it exists as a directory already),
        `None` is returned.
        """
        if self._base_dir:
            abs_fn = os.path.abspath(os.path.join(self._base_dir, filename))
        else:
            abs_fn = os.path.abspath(filename)

        out_dir = os.path.dirname(abs_fn)
        if not os.path.exists(out_dir):
            logging.info(f'<{self.name}> Output directory {out_dir} does not exist and will be created')
            os.makedirs(out_dir, exist_ok=True)

        if os.path.exists(abs_fn) and not os.path.isfile(abs_fn):
            logging.error(f'<{self.name}> Output file {abs_fn} is not a file')
            return None

        elif os.path.exists(abs_fn):
            logging.warning(f'<{self.name}> Output file {abs_fn} exists and will be overwritten')

        return abs_fn

    def collectLabels(self, doc: 'App.Document', labels: list[str]) -> list[object]:
        """Collect objects by Label for the export operation.

        The `labels` parameter must be a list of FreeCAD object labels to look
        up. Subclasses may implement the `_checkItem` method to verify that any
        objects found by their label are able to be exported by this runner.

        If a label appears in the list more than once, the associated object
        will also be returned more than once, which may result in unexpected
        behavior. A warning will be written to the log in this case.
        """
        slabels = set()
        items = []

        for lbl in labels:
            if lbl in slabels:
                logging.warning(f'<{self.name}> Duplicate label {lbl} included for export')

            slabels.add(lbl)
            objs = doc.getObjectsByLabel(lbl)
            if not objs:
                logging.warning(f'<{self.name}> No object found with label {lbl}')
                continue

            if len(objs) > 1:
                logging.warning(f'<{self.name}> Multiple objects found with label {lbl}')

            for obj in objs:
                if self._checkItem(obj):
                    items.append(obj)

        return items

    def collectPages(self, doc: 'App.Document') -> list[object]:
        """Collect all TechDraw::DrawingPage items for the export operation.

        Subclasses may implement the `_checkItem` method to verify that any
        objects are able to be exported by this runner.
        """
        items = []
        for obj in doc.Objects:
            if obj.TypeId != 'TechDraw::DrawPage':
                continue

            if self._checkItem(obj):
                items.append(obj)

        return items

    def collectShapes(self, doc: 'App.Document') -> list[object]:
        """Collect all drawing items with a `Shape` for the export operation.

        This method is a little complicated since shapes can in general contain
        other shapes. When a shape is found, its ownership tree is traversed up
        to find the highest parent object that still has a `Shape` attribute,
        and that parent object is used in the returned set. Parent objects are
        included only once based on their `Name` attribute, so this method will
        not export a shape more than once.

        Subclasses may implement the `_checkItem` method to verify that any
        objects are able to be exported by this runner.
        """
        items = []
        names = set()

        def findTopParents(obj: object) -> list[object]:
            if not obj.Parents:
                return [ obj ]

            parents = []
            for p, _ in obj.Parents:
                parents.extend(findTopParents(p))

            return parents

        for obj in doc.Objects:
            if not hasattr(obj, 'Shape'):
                continue

            parents = findTopParents(obj)
            logging.debug(f'<{self.name}> Found parents {[p.Name for p in parents]} for {obj.Name}')

            for p in parents:
                if p.Name in names:
                    continue

                if self._checkItem(p):
                    names.add(p.Name)
                    items.append(p)

        return items

    def collect(self, doc: 'App.Document') -> list[object]:
        """Collect items for the export operation.

        This uses the `objects` output configuration key to call `collectPages`,
        `collectShapes`, or `collectLabels` to get the set of objects to export.
        Subclasses may implement the `_checkItem` method to verify that any
        objects are able to be exported by this runner.
        """
        if isinstance(self._config.objects, list):
            logging.debug(f'<{self.name}> Collecting outputs by label')
            return self.collectLabels(doc, self._config.objects)

        elif isinstance(self._config.objects, FCBotAllPages):
            logging.debug(f'<{self.name}> Collecting all pages as output')
            return self.collectPages(doc)

        elif isinstance(self._config.objects, FCBotAllShapes):
            logging.debug(f'<{self.name}> Collecting all shapes as output')
            return self.collectShapes(doc)

        else:
            raise TypeError(f'Unexpected value for "{self._config.name}.outputs"')

    def emit(self, base_dir: Optional[str] = None) -> str:
        """Generate a Python Script representation of this Runner.
        
        This generates a Python code snippet that will construct this Runner
        within the FreeCAD run context using a JSON representation of the
        configuration data. This method should not be overridden by subclasses
        unless absolutely necessary to support an object type that is not
        supported by standard JSON.

        In practice it would probably work to just call
        `repr(self._config.model_dump())` instead of requiring intermediate
        JSON representation, but this provides some level of type safety.
        """
        config_json = self._config.model_dump_json(by_alias=True)
        return f'load_runner_json({repr(config_json)}, {repr(self.name)}, base_dir={repr(base_dir or self._base_dir)})'

    def run(self, doc: 'App.Document') -> None:
        """Run the Output Runner."""
        msg = f'Running {self.name}'
        if self.comment:
            msg += f' ({self.comment})'

        logging.info(msg)
        
        # Collect input objects
        items = self.collect(doc)
        if not items:
            logging.warning(f'<{self.name}> No items were collected for processing')
            return

        logging.debug(f'<{self.name}> Collected {len(items)} objects for processing: {[i.Label for i in items]}')

        # Run the output processing
        self._execute(doc, items)
        logging.info(f'<{self.name}> Completed')

    def __repr__(self) -> str:
        """Generate a representation of this Runner."""
        return f'<{self.__class__.__name__} {self.name}>'

    @property
    def comment(self) -> str | None:
        return self._config.comment

    @property
    def filename(self) -> str:
        return self._config.filename

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def output_type(self) -> str:
        return self._type
