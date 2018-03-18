"""Tests for bag.web.burla."""

from bag.web.burla import Page


def test_Page_url():
    p = Page(op_name='test_page',
             url_templ='user/:user_id/address/:address_id')
    assert 'user/1/address/2' == p.url(user_id=1, address_id=2)

    p = Page(op_name='test2', url_templ='user/:user_id/address/:address_id')
    assert p.url(user_id=3, address_id=2, showmap=1, make='coffee') \
        in ('user/3/address/2?showmap=1&make=coffee',
            'user/3/address/2?make=coffee&showmap=1')

    p = Page('test3', url_templ='user/:user_id/address/:address_id')
    adict = dict(user_id=3, address_id=2, showmap=1, fragment='make_coffee')
    assert 'user/3/address/2?showmap=1#make_coffee' == p.url(**adict)
    assert 4 == len(adict)  # The original dict is not modified by the function
