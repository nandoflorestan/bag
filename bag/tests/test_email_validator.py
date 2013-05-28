#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Tests the module email_validator.py'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import unittest
from bag.email_validator import DomainValidator, EmailValidator


class TestEmailValidator(unittest.TestCase):
    def test_domain_validator(self):
        d = DomainValidator()
        domain, err = d.validate('acentuação.com')
        assert not err
        domain, err = d.validate('tld.ácçênts')
        assert not err
        domain, err = d.validate(
            'subdomain.subdomain.subdomain.sub.domain.tld')
        assert not err
        domain, err = d.validate('.com')
        assert err

    def test_email_validator(self):
        v = EmailValidator()
        # Correct email addresses
        email, err = v.validate('Dmitry.Shostakovich@great-music.com')
        assert not err
        email, err = v.validate('  ha@ha.ha  ')
        assert not err
        email, err = v.validate("a.a-a+a_a!a#a$a%a&a'a/a=a`a|a~a?a^a{a}"
                                "a*a@special.chars")
        assert not err
        email, err = v.validate('user+mailbox@example.com')
        assert not err
        email, err = v.validate('customer/department=shipping@example.com')
        assert not err
        email, err = v.validate('$A12345@example.com')
        assert not err
        email, err = v.validate('!def!xyz%abc@example.com')
        assert not err
        email, err = v.validate('_somename@example.com')
        assert not err
        # Incorrect email addresses
        email, err = v.validate('Abc.example.com')
        assert err
        email, err = v.validate('A@b@example.com')
        assert err
        email, err = v.validate('Abc.@example.com')
        assert err
        email, err = v.validate('Abc..123@example.com')
        assert err
        email, err = v.validate('ã@example.com')
        assert err
        email, err = v.validate('\@example.com')
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
