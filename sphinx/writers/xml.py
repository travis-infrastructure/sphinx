"""
    sphinx.writers.xml
    ~~~~~~~~~~~~~~~~~~

    Docutils-native XML and pseudo-XML writers.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils.writers.docutils_xml import Writer as BaseXMLWriter

if False:
    # For type annotation
    from typing import Any, Tuple  # NOQA
    from sphinx.builders import Builder  # NOQA


class XMLWriter(BaseXMLWriter):

    def __init__(self, builder):
        # type: (Builder) -> None
        super().__init__()
        self.builder = builder
        self.translator_class = self.builder.get_translator_class()

    def translate(self, *args, **kwargs):
        # type: (Any, Any) -> None
        self.document.settings.newlines = \
            self.document.settings.indents = \
            self.builder.env.config.xml_pretty
        self.document.settings.xml_declaration = True
        self.document.settings.doctype_declaration = True
        return super().translate()


class PseudoXMLWriter(BaseXMLWriter):

    supported = ('pprint', 'pformat', 'pseudoxml')
    """Formats this writer supports."""

    config_section = 'pseudoxml writer'
    config_section_dependencies = ('writers',)

    output = None
    """Final translated form of `document`."""

    def __init__(self, builder):
        # type: (Builder) -> None
        super().__init__()
        self.builder = builder

    def translate(self):
        # type: () -> None
        self.output = self.document.pformat()

    def supports(self, format):
        # type: (str) -> bool
        """This writer supports all format-specific elements."""
        return True
