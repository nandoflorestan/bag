#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tests the module email_validator.py'''

from __future__ import absolute_import
from __future__ import unicode_literals  # unicode by default
import unittest
from bag.email_validator import (DomainValidator,
    EmailValidator, EmailHarvester)


class TestEmailValidator(unittest.TestCase):
    def test_domain_validator(self):
        d = DomainValidator()
        domain, err = d.validate(u'acentuação.com')
        assert not err
        domain, err = d.validate(u'tld.ácçênts')
        assert not err
        domain, err = d.validate(
            u'subdomain.subdomain.subdomain.sub.domain.tld')
        assert not err
        domain, err = d.validate(u'.com')
        assert err

    def test_email_validator(self):
        v = EmailValidator()
        # Correct email addresses
        email, err = v.validate(u'Dmitry.Shostakovich@great-music.com')
        assert not err
        email, err = v.validate(u'  ha@ha.ha  ')
        assert not err
        email, err = v.validate(u"a.a-a+a_a!a#a$a%a&a'a/a=a`a|a~a?a^a{a}" \
                                 u"a*a@special.chars")
        assert not err
        email, err = v.validate(u'user+mailbox@example.com')
        assert not err
        email, err = v.validate(u'customer/department=shipping@example.com')
        assert not err
        email, err = v.validate(u'$A12345@example.com')
        assert not err
        email, err = v.validate(u'!def!xyz%abc@example.com')
        assert not err
        email, err = v.validate(u'_somename@example.com')
        assert not err
        # Incorrect email addresses
        email, err = v.validate(u'Abc.example.com')
        assert err
        email, err = v.validate(u'A@b@example.com')
        assert err
        email, err = v.validate(u'Abc.@example.com')
        assert err
        email, err = v.validate(u'Abc..123@example.com')
        assert err
        email, err = v.validate(u'ã@example.com')
        assert err
        email, err = v.validate(u'\@example.com')
        assert err


if __name__ == '__main__':  # Interactive test
    v = EmailValidator(lookup_dns='a')
    while True:
        email = \
            raw_input('Type an email or CTRL-C to quit: ').decode('utf8')
        email, err = v.validate(email)
        if err:
            print('Error: ' + err)
        else:
            print('E-mail is valid: ' + email)  # the email, corrected
