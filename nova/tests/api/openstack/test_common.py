# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Test suites for 'common' code used throughout the OpenStack HTTP API.
"""

import webob.exc

from webob import Request

from nova import test
from nova.api.openstack import common


class LimiterTest(test.TestCase):
    """
    Unit tests for the `nova.api.openstack.common.limited` method which takes
    in a list of items and, depending on the 'offset' and 'limit' GET params,
    returns a subset or complete set of the given items.
    """

    def setUp(self):
        """ Run before each test. """
        super(LimiterTest, self).setUp()
        self.tiny = range(1)
        self.small = range(10)
        self.medium = range(1000)
        self.large = range(10000)

    def test_limiter_offset_zero(self):
        """ Test offset key works with 0. """
        req = Request.blank('/?offset=0')
        self.assertEqual(common.limited(self.tiny, req), self.tiny)
        self.assertEqual(common.limited(self.small, req), self.small)
        self.assertEqual(common.limited(self.medium, req), self.medium)
        self.assertEqual(common.limited(self.large, req), self.large[:1000])

    def test_limiter_offset_medium(self):
        """ Test offset key works with a medium sized number. """
        req = Request.blank('/?offset=10')
        self.assertEqual(common.limited(self.tiny, req), [])
        self.assertEqual(common.limited(self.small, req), self.small[10:])
        self.assertEqual(common.limited(self.medium, req), self.medium[10:])
        self.assertEqual(common.limited(self.large, req), self.large[10:1010])

    def test_limiter_offset_over_max(self):
        """ Test offset key works with a number over 1000 (max_limit). """
        req = Request.blank('/?offset=1001')
        self.assertEqual(common.limited(self.tiny, req), [])
        self.assertEqual(common.limited(self.small, req), [])
        self.assertEqual(common.limited(self.medium, req), [])
        self.assertEqual(
            common.limited(self.large, req), self.large[1001:2001])

    def test_limiter_offset_blank(self):
        """ Test offset key works with a blank offset. """
        req = Request.blank('/?offset=')
        self.assertRaises(
            webob.exc.HTTPBadRequest, common.limited, self.tiny, req)

    def test_limiter_offset_bad(self):
        """ Test offset key works with a BAD offset. """
        req = Request.blank(u'/?offset=\u0020aa')
        self.assertRaises(
            webob.exc.HTTPBadRequest, common.limited, self.tiny, req)

    def test_limiter_nothing(self):
        """ Test request with no offset or limit """
        req = Request.blank('/')
        self.assertEqual(common.limited(self.tiny, req), self.tiny)
        self.assertEqual(common.limited(self.small, req), self.small)
        self.assertEqual(common.limited(self.medium, req), self.medium)
        self.assertEqual(common.limited(self.large, req), self.large[:1000])

    def test_limiter_limit_zero(self):
        """ Test limit of zero. """
        req = Request.blank('/?limit=0')
        self.assertEqual(common.limited(self.tiny, req), self.tiny)
        self.assertEqual(common.limited(self.small, req), self.small)
        self.assertEqual(common.limited(self.medium, req), self.medium)
        self.assertEqual(common.limited(self.large, req), self.large[:1000])

    def test_limiter_limit_medium(self):
        """ Test limit of 10. """
        req = Request.blank('/?limit=10')
        self.assertEqual(common.limited(self.tiny, req), self.tiny)
        self.assertEqual(common.limited(self.small, req), self.small)
        self.assertEqual(common.limited(self.medium, req), self.medium[:10])
        self.assertEqual(common.limited(self.large, req), self.large[:10])

    def test_limiter_limit_over_max(self):
        """ Test limit of 3000. """
        req = Request.blank('/?limit=3000')
        self.assertEqual(common.limited(self.tiny, req), self.tiny)
        self.assertEqual(common.limited(self.small, req), self.small)
        self.assertEqual(common.limited(self.medium, req), self.medium)
        self.assertEqual(common.limited(self.large, req), self.large[:1000])

    def test_limiter_limit_and_offset(self):
        """ Test request with both limit and offset. """
        items = range(2000)
        req = Request.blank('/?offset=1&limit=3')
        self.assertEqual(common.limited(items, req), items[1:4])
        req = Request.blank('/?offset=3&limit=0')
        self.assertEqual(common.limited(items, req), items[3:1003])
        req = Request.blank('/?offset=3&limit=1500')
        self.assertEqual(common.limited(items, req), items[3:1003])
        req = Request.blank('/?offset=3000&limit=10')
        self.assertEqual(common.limited(items, req), [])

    def test_limiter_custom_max_limit(self):
        """ Test a max_limit other than 1000. """
        items = range(2000)
        req = Request.blank('/?offset=1&limit=3')
        self.assertEqual(
            common.limited(items, req, max_limit=2000), items[1:4])
        req = Request.blank('/?offset=3&limit=0')
        self.assertEqual(
            common.limited(items, req, max_limit=2000), items[3:])
        req = Request.blank('/?offset=3&limit=2500')
        self.assertEqual(
            common.limited(items, req, max_limit=2000), items[3:])
        req = Request.blank('/?offset=3000&limit=10')
        self.assertEqual(common.limited(items, req, max_limit=2000), [])

    def test_limiter_negative_limit(self):
        """ Test a negative limit. """
        req = Request.blank('/?limit=-3000')
        self.assertRaises(
            webob.exc.HTTPBadRequest, common.limited, self.tiny, req)

    def test_limiter_negative_offset(self):
        """ Test a negative offset. """
        req = Request.blank('/?offset=-30')
        self.assertRaises(
            webob.exc.HTTPBadRequest, common.limited, self.tiny, req)


class PaginationParamsTest(test.TestCase):
    """
    Unit tests for the `nova.api.openstack.common.get_pagination_params`
    method which takes in a request object and returns 'marker' and 'limit'
    GET params.
    """

    def test_no_params(self):
        """ Test no params. """
        req = Request.blank('/')
        self.assertEqual(common.get_pagination_params(req), {})

    def test_valid_marker(self):
        """ Test valid marker param. """
        req = Request.blank('/?marker=1')
        self.assertEqual(common.get_pagination_params(req), {'marker': 1})

    def test_invalid_marker(self):
        """ Test invalid marker param. """
        req = Request.blank('/?marker=-2')
        self.assertRaises(
            webob.exc.HTTPBadRequest, common.get_pagination_params, req)

    def test_valid_limit(self):
        """ Test valid limit param. """
        req = Request.blank('/?limit=10')
        self.assertEqual(common.get_pagination_params(req), {'limit': 10})

    def test_invalid_limit(self):
        """ Test invalid limit param. """
        req = Request.blank('/?limit=-2')
        self.assertRaises(
            webob.exc.HTTPBadRequest, common.get_pagination_params, req)

    def test_valid_limit_and_marker(self):
        """ Test valid limit and marker parameters. """
        req = Request.blank('/?limit=20&marker=40')
        self.assertEqual(common.get_pagination_params(req),
                         {'marker': 40, 'limit': 20})


class MiscFunctionsTest(test.TestCase):

    def test_remove_version_from_href(self):
        fixture = 'http://www.testsite.com/v1.1/images'
        expected = 'http://www.testsite.com/images'
        actual = common.remove_version_from_href(fixture)
        self.assertEqual(actual, expected)

    def test_remove_version_from_href_2(self):
        fixture = 'http://www.testsite.com/v1.1/'
        expected = 'http://www.testsite.com/'
        actual = common.remove_version_from_href(fixture)
        self.assertEqual(actual, expected)

    def test_remove_version_from_href_3(self):
        fixture = 'http://www.testsite.com/v10.10'
        expected = 'http://www.testsite.com'
        actual = common.remove_version_from_href(fixture)
        self.assertEqual(actual, expected)

    def test_remove_version_from_href_4(self):
        fixture = 'http://www.testsite.com/v1.1/images/v10.5'
        expected = 'http://www.testsite.com/images/v10.5'
        actual = common.remove_version_from_href(fixture)
        self.assertEqual(actual, expected)

    def test_remove_version_from_href_bad_request(self):
        fixture = 'http://www.testsite.com/1.1/images'
        self.assertRaises(ValueError,
                          common.remove_version_from_href,
                          fixture)

    def test_remove_version_from_href_bad_request_2(self):
        fixture = 'http://www.testsite.com/v/images'
        self.assertRaises(ValueError,
                          common.remove_version_from_href,
                          fixture)

    def test_remove_version_from_href_bad_request_3(self):
        fixture = 'http://www.testsite.com/v1.1images'
        self.assertRaises(ValueError,
                          common.remove_version_from_href,
                          fixture)

    def test_get_id_from_href(self):
        fixture = 'http://www.testsite.com/dir/45'
        actual = common.get_id_from_href(fixture)
        expected = 45
        self.assertEqual(actual, expected)

    def test_get_id_from_href_bad_request(self):
        fixture = 'http://45'
        self.assertRaises(ValueError,
                          common.get_id_from_href,
                          fixture)

    def test_get_uuid_from_href(self):
        fixture = 'http://www.testsite.com/dir/45'
        actual = common.get_uuid_from_href(fixture)
        expected = '45'
        self.assertEqual(actual, expected)

    def test_get_uuid_from_href_bad_request(self):
        fixture = 'http://'
        self.assertRaises(ValueError,
                          common.get_uuid_from_href,
                          fixture)
