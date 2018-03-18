"""Spreadsheet importers in CSV and Excel formats.

The basic premise is that the spreadsheet to be imported will have
headers on the first row -- some of which are mandatory.

The headers are used to map the data to a dynamically-generated class so
**each spreadsheet row is seen, in your code, as an object
(mapping columns to their values)**.

The code in this __init__ module is used in the inner modules.
"""

try:
    from bag.web.pyramid import _
except ImportError:
    _ = str  # and i18n is disabled.


class MissingHeaders(Exception):

    msg1 = _('The spreadsheet is missing the required header: ')
    msg2 = _('The spreadsheet is missing the required headers: ')

    def __init__(self, missing_headers):
        self.missing_headers = missing_headers

    def __repr__(self):
        return '<{} {}>'.format(type(self).__name__, self.missing_headers)

    def __str__(self):
        if len(self.missing_headers) == 1:
            return self.msg1 + self.missing_headers[0]
        else:
            return self.msg2 + ', '.join([
                '"{}"'.format(h) for h in self.missing_headers])


class ForbiddenHeaders(Exception):

    msg1 = _('The spreadsheet contains the forbidden header: ')
    msg2 = _('The spreadsheet contains the forbidden headers: ')

    def __init__(self, forbidden_headers):
        self.forbidden_headers = forbidden_headers

    def __repr__(self):
        return '<{} {}>'.format(type(self).__name__, self.forbidden_headers)

    def __str__(self):
        if len(self.forbidden_headers) == 1:
            return self.msg1 + self.forbidden_headers[0]
        else:
            return self.msg2 + ', '.join(['"{}"'.format(h) for h in self.forbidden_headers])


def raise_if_missing_required_headers(headers, required_headers=[],
                                      case_sensitive=False):
    """Ensure all ``required_headers`` are present in ``headers``.

    Else raise MissingHeaders.
    """
    if not case_sensitive:
        headers = [h.lower() if h else None for h in headers]
        missing_headers = [h for h in required_headers
                           if h.lower() not in headers]
    else:
        missing_headers = [h for h in required_headers if h not in headers]

    if missing_headers:
        raise MissingHeaders(missing_headers)


def raise_if_forbidden_headers(headers, forbidden_headers=[],
                               case_sensitive=False):
    """Ensure all ``forbidden_headers`` are not present in ``headers``.

    Else raise ForbiddenHeaders.
    """
    if not case_sensitive:
        headers = [h.lower() if h else None for h in headers]
        blocked_headers = [
            h for h in forbidden_headers if h.lower() in headers]
    else:
        blocked_headers = [h for h in forbidden_headers if h in headers]

    if blocked_headers:
        raise ForbiddenHeaders(blocked_headers)


def get_corresponding_variable_names(headers, required_headers,
                                     case_sensitive=False):
    """Return variable names corresponding to the legible headers.

    The parameter ``required_headers`` may be a map or a sequence. If map,
    the keys should be the legible header names and the values should be
    the corresponding variable names.  For headers absent from the map,
    or if ``required_headers`` is a list, the variable names returned
    are the result of string conversion.
    """
    if not case_sensitive:
        headers = [h.lower() if h else None for h in headers]
        required_headers = [h.lower() for h in required_headers]
    vars = []
    for header in headers:
        if header is None:
            vars.append(None)
            continue
        var = None
        if hasattr(required_headers, 'get'):
            var = required_headers.get(header.strip())
        if not var:
            var = header.strip().replace(' ', '_').replace('-', '_').lower()
        vars.append(var)
    return vars
