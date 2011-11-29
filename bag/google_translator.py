#!/usr/bin/env python
# -*- coding: utf-8 -*-

# http://code.google.com/apis/ajaxlanguage/terms.html
# http://code.google.com/apis/ajaxlanguage/

import sys
from urllib import urlopen, urlencode, quote


# A typical response from Google Translate is:
# {"responseData": {"translatedText":"Onde é que eu deixe o meu Snickers?"},
#  "responseDetails": null, "responseStatus": 200}
# To easily parse this, we define "null" here:
null = None


class GoogleTranslator(object):
    """Typical usage:
    g = GoogleTranslator("en", "pt")
    g.translate("This parrot is deceased.")

    Or from the command line:
    ./google_translator.py en es "It is a late parrot."
    """

    URL = "http://ajax.googleapis.com/ajax/services/language/translate" \
          "?v=1.0&langpair="

    def __init__(self, from_lang, to_lang):
        # TODO: Validate language pair: http://code.google.com/p/google-api-translate-java/source/browse/trunk/src/com/google/api/translate/Language.java
        self.from_lang = from_lang
        self.to_lang = to_lang
        self.url = self.URL + from_lang + "%7C" + to_lang + "&q="

    def translate(self, text):
        url = self.url + quote(text)
        file = urlopen(url)
        t = file.read()
        exec("d = " + t)
        if d["responseStatus"] != 200:
            print(d)
            raise RuntimeError("Translation error: " \
                + d.get("responseDetails", "") + ". Status: " \
                + str(d.get("responseStatus", "")))
        return d["responseData"]["translatedText"]

    def utranslate(self, text):
        """Returns the translation as a Unicode object."""
        return self.translate(text).decode("utf8")


__doc__ = GoogleTranslator.__doc__

if __name__ == '__main__':
    g = GoogleTranslator(sys.argv[1], sys.argv[2])
    print(g.translate(sys.argv[3]))
