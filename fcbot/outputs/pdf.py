"""FreeCAD PDF Output Classes.

Copyright (c) 2025 Asymworks, LLC.
All Rights Reserved.
"""

import logging
import os
import shutil
import tempfile

from typing import Any, Optional

from .base import OutputRunner


class PdfOutputRunner(OutputRunner):
    """Export PDF files from FreeCAD TechDraw Pages."""
    def __init__(self, config: dict[str, Any], *, base_dir: Optional[str] = None):
        super().__init__(config, base_dir=base_dir)

    def _checkItem(self, item: object) -> bool:
        """Check that the items are `TechDraw::DrawPage` items."""
        if item.TypeId != 'TechDraw::DrawPage':
            logging.debug(f'<{self.name}> Object {item.Label} is not a TechDraw::DrawPage')
            return False

        return True

    def _execute(self, doc: 'App.Document', items: list[object]) -> None:
        """Export `TechDraw::DrawPage` objects to a PDF file."""
        from pypdf import PdfReader, PdfWriter

        import FreeCADGui
        import TechDrawGui

        if not items:
            logging.warning(f'<{self.name}> Empty item list passed to _execute()')
            return

        for obj in items:
            if obj.TypeId != 'TechDraw::DrawPage':
                logging.error(f'<{self.name}> Object "{obj.Label}" is not a TechDraw::DrawPage')
                return

            logging.debug(f'<{self.name}> Redrawing page {obj.Label}')
            obj.recompute(True)

        FreeCADGui.updateGui()

        abs_fn = self.checkOutputFile(self.filename)
        with tempfile.TemporaryDirectory() as export_dir:
            logging.debug(f'<{self.name}> Using temporary export directory {export_dir}')

            try:
                if len(items) == 1:
                    export_fn = os.path.join(export_dir, 'export.pdf')

                    logging.info(f'<{self.name}> Exporting {items[0].Label} as PDF to {abs_fn}')
                    TechDrawGui.exportPageAsPdf(items[0], export_fn)
                    if not os.path.isfile(export_fn):
                        logging.error(f'<{self.name}> FreeCAD did not generate export file {export_fn}')
                        return

                    logging.debug(f'<{self.name}> Renaming {export_fn} to {abs_fn}')
                    shutil.copy(export_fn, abs_fn)
                    os.unlink(export_fn)

                else:
                    page_fns = []
                    for pg_item in items:
                        export_fn = os.path.join(export_dir, f'{pg_item.Label}.pdf')
                        page_fns.append(export_fn)

                        logging.info(f'<{self.name}> Exporting {pg_item.Label} as PDF to {pg_item.Label}.pdf')
                        TechDrawGui.exportPageAsPdf(pg_item, export_fn)
                        if not os.path.isfile(export_fn):
                            logging.error(f'<{self.name}> FreeCAD did not generate export file {export_fn}')
                            return

                    logging.info(f'<{self.name}> Merging {len(page_fns)} files into single PDF to {self.filename}')

                    writer = PdfWriter()
                    for pdf_fn in page_fns:
                        with open(pdf_fn, 'rb') as f:
                            reader = PdfReader(f)
                            if reader.get_num_pages() != 1:
                                logging.warning(f'<{self.name}> Exported PDF file for {os.path.basename(pdf_fn)} has more than 1 page')
                            for i, page in enumerate(reader.pages):
                                logging.debug(f'<{self.name}> Appending page {i+1} from {pdf_fn}')
                                writer.add_page(page)

                    with open(abs_fn, 'wb') as f:
                        logging.debug(f'<{self.name}> Writing merged PDF data to {abs_fn}')
                        writer.write(f)

            except Exception as e:
                logging.error(f'<{self.name}> Failed to export to PDF: {repr(e)}')
