#!/usr/bin/env python3

"""reStructuredText document validator / verifier / checker.

For Python code you have 2 available functions::

    warnings = check_rst_document(a_string)
    warnings = check_rst_file(path)

These functions will return an empty list if the document is OK.

In shell, use it like this::

    check_rst < some_document.rst

Or like this if the package *bag* isn't easy_installed:

    python check_rst.py < some_document.rst

The command prints either "OK" or the warnings.
And it returns 0 if the document is OK.
"""

import codecs
from docutils.parsers.rst import Parser  # type: ignore
from docutils import utils  # type: ignore
# from docutils.readers.standalone import Reader
from docutils.transforms import (
    frontmatter, misc, references, universal, writer_aux)

# TODO: I don't know if the order of these transforms makes any sense.
check_transforms = [
    # from parsers/rst/__init__.py:
    universal.SmartQuotes,
    # from readers/__init__.py:
    universal.Decorations,
    universal.ExposeInternals,
    universal.StripComments,
    # from readers/standalone.py:
    references.Substitutions,
    references.PropagateTargets,
    frontmatter.DocTitle,
    frontmatter.SectionSubTitle,
    frontmatter.DocInfo,
    references.AnonymousHyperlinks,
    references.IndirectHyperlinks,
    references.Footnotes,
    references.ExternalTargets,
    references.InternalTargets,
    references.DanglingReferences,
    misc.Transitions,
    # from writers/__init__.py:
    universal.Messages,
    universal.FilterMessages,
    universal.StripClassesAndElements,
    # from writers/html4css1/__init__.py:
    writer_aux.Admonitions,
]


def check_rst_document(source, source_path='<string>', settings=None):
    """Return a list of objects containing problems in a rst document.

    Provide the reStructuredText document through the argument ``source``.

    ``settings`` is the settings object for the docutils document instance.
    If None, the default settings are used.
    """
    alist = []

    def accumulate(x):
        return alist.append(x)
    document = utils.new_document(source_path, settings=settings)
    document.reporter.attach_observer(accumulate)
    if settings is None:  # Fill in some values to prevent AttributeError
        document.settings.tab_width = 8
        document.settings.pep_references = None
        document.settings.rfc_references = None
        document.settings.smart_quotes = True
        document.settings.smartquotes_locales = ['en']
        document.settings.file_insertion_enabled = True
    parser = Parser()
    parser.parse(source, document)
    # Now apply transforms to get more warnings
    document.transformer.add_transforms(check_transforms)
    document.transformer.apply_transforms()
    return alist


def check_rst_file(path, encoding='utf-8', settings=None):
    with codecs.open(path, encoding=encoding) as stream:
        source = stream.read()
    return check_rst_document(source, path, settings=settings)


"""
# ANOTHER WAY would be to detect docinfo printing out a warning when
# publish_parts() executes. But that would only work as a command, not as
# a Python function, I am right?
def check_rst_file2(path, encoding='utf-8'):
    from docutils.core import publish_parts
    with codecs.open(path, encoding=encoding) as stream:
        source = stream.read()
    adict = publish_parts(source, writer_name='html')
    # <string>:72: (ERROR/3) Unknown target name: "read the source code".
"""


""" The following attempt isn't finished, the docutils API is too convoluted:
class RestDocumentChecker(Reader):
    '''Has parse warnings accumulated into its ``checker_result``
        instance variable.
        '''
    def new_document(self):
        # We override this method in order to be able to observe the document
        document = super(RestDocumentChecker, self).new_document()
        self.checker_result = []
        accumulate = lambda x: self.checker_result.append(x)
        document.reporter.attach_observer(accumulate)
        return document


def check_rst_file2(path, encoding='utf-8', settings=None):
    '''Returns a list of objects containing (in their ``message`` attribute)
        problems in the provided reStructuredText document ``source``.

        ``settings`` is the settings object for the docutils document instance.
        If None, the default settings are used.
        '''
    r = RestDocumentChecker(parser=Parser())
    with codecs.open(path, encoding=encoding) as stream:
        r.read(stream, None, None)
    return r.checker_result
"""


def command():
    """Entry point; becomes a console script when the package is installed."""
    from sys import exit, stdin
    source = stdin.read()
    warnings = check_rst_document(source)
    if warnings:
        print('\nHere are the warnings for that rst document:')
        for w in warnings:
            print('    ' + str(w))
        exit(1)
    else:
        print('OK')
        exit(0)


if __name__ == '__main__':
    command()
