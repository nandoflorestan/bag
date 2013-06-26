# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import unittest
from nine import str, IS_PYTHON2
from bag.web.web_deps import DepsRegistry, Dependency, WebDeps


class TestDepsRegistry(unittest.TestCase):
    def test_summon(self):
        reg = DepsRegistry()
        all = Dependency('montão', deps='n, m, b, a')

        if IS_PYTHON2:
            self.assertEqual(repr(all), b'Dependency("mont\xc3\xa3o")')
        else:
            self.assertEqual(repr(all), 'Dependency("montão")')

        self.assertEqual(str(all), 'montão')
        n = Dependency('n', deps='b, m')
        m = Dependency('m', deps='a')
        a = Dependency('a')
        b = Dependency('b')
        reg.admit(all, n, m, a, b)
        reg.close()
        self.assertEqual(reg.summon('a'), [a])
        self.assertEqual(reg.summon('b'), [b])
        self.assertEqual(reg.summon('m'), [a, m])
        self.assertEqual(reg.summon('n'), [a, m, b, n])
        self.assertEqual(reg.summon('m, b'), [b, a, m])
        self.assertEqual(reg.summon('montão'), [a, b, m, n, all])
        self.assertEqual(reg.summon('montão,a,b,m,n'), [a, m, b, n, all])


class TestPageDeps(unittest.TestCase):
    def setUp(self):
        deps = WebDeps()
        deps.lib('jquery.ui', url='/static/lib/jquery-ui-1.8.16.min.js',
            deps='jquery')
        deps.lib('jquery', url="/static/lib/jquery-1.7.1.min.js")
        deps.lib('deform', url="/static/lib/deform.js",
            deps='jquery, jquery.ui')
        deps.css('jquery', url='http://jquery.css')
        deps.css('deform', url='http://deform.css', deps='jquery.ui')
        deps.css('jquery.ui', url='http://jquery.ui.css', deps='jquery')
        deps.package('jquery.ui', libs='jquery.ui',
            css='jquery.ui', script='alert("JQuery UI spam!");')
        deps.package('deform', deps='jquery.ui', libs='deform',
            css='deform', script='alert("Deform spam!");')
        self.PageDeps = deps.close()

    def test_request1(self):
        deps = self.PageDeps()
        deps.lib('jquery')
        self.assertEqual(deps.lib.urls, ['/static/lib/jquery-1.7.1.min.js'])
        deps.css('jquery')
        self.assertEqual(deps.css.urls, ['http://jquery.css'])
        deps.script('alert("Bruhaha");')
        self.assertEqual(deps.script.tags, '<script type="text/javascript">'
            '\nalert("Bruhaha");\n</script>\n')

    def test_request2(self):
        deps = self.PageDeps()
        deps.lib('jquery.ui')
        deps.lib('jquery.ui')  # requiring twice should have no effect
        SCRIPTS_OUT = '<script type="text/javascript" ' \
            'src="/static/lib/jquery-1.7.1.min.js"></script>\n' \
            '<script type="text/javascript" ' \
            'src="/static/lib/jquery-ui-1.8.16.min.js"></script>'
        self.assertEqual(deps.lib.tags, SCRIPTS_OUT)
        deps.css('deform')
        CSS_OUT = '<link rel="stylesheet" ' \
            'type="text/css" href="http://jquery.css" />\n' \
            '<link rel="stylesheet" type="text/css" '\
            'href="http://jquery.ui.css" />\n' \
            '<link rel="stylesheet" type="text/css" ' \
            'href="http://deform.css" />'
        self.assertEqual(deps.css.tags, CSS_OUT)
        ALERT = 'alert("Bruhaha");'
        deps.script(ALERT)
        deps.script(ALERT)  # Repeating should have no effect
        ALERT_OUT = '<script type="text/javascript">' \
            '\nalert("Bruhaha");\n</script>\n'
        self.assertEqual(deps.script.tags, ALERT_OUT)
        self.assertEqual(deps.top_output, CSS_OUT)
        self.assertEqual(deps.bottom_output, SCRIPTS_OUT + '\n' + ALERT_OUT)
        self.assertEqual(str(deps),
            '\n'.join([CSS_OUT, SCRIPTS_OUT, ALERT_OUT]))

    def test_request3(self):
        deps = self.PageDeps()
        deps.lib('deform, jquery')
        deps.lib('jquery')
        self.assertEqual(deps.lib.urls, ['/static/lib/jquery-1.7.1.min.js',
            '/static/lib/jquery-ui-1.8.16.min.js', "/static/lib/deform.js"])

    def test_package1(self):
        deps = self.PageDeps()
        deps.package('jquery.ui')
        deps.package('jquery.ui')  # Repeating should have no effect
        self.assertEqual(str(deps), '''
<link rel="stylesheet" type="text/css" href="http://jquery.css" />
<link rel="stylesheet" type="text/css" href="http://jquery.ui.css" />
<script type="text/javascript" src="/static/lib/jquery-1.7.1.min.js"></script>
<script type="text/javascript" src="/static/lib/jquery-ui-1.8.16.min.js">\
</script>
<script type="text/javascript">
alert("JQuery UI spam!");
</script>\n'''.lstrip())

    def test_package2(self):
        deps = self.PageDeps()
        deps.package('deform')
        self.assertEqual(str(deps), '''
<link rel="stylesheet" type="text/css" href="http://jquery.css" />
<link rel="stylesheet" type="text/css" href="http://jquery.ui.css" />
<link rel="stylesheet" type="text/css" href="http://deform.css" />
<script type="text/javascript" src="/static/lib/jquery-1.7.1.min.js"></script>
<script type="text/javascript" src="/static/lib/jquery-ui-1.8.16.min.js">\
</script>
<script type="text/javascript" src="/static/lib/deform.js"></script>
<script type="text/javascript">
alert("JQuery UI spam!");
alert("Deform spam!");
</script>\n'''.lstrip())
