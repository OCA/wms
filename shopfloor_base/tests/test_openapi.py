# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common_misc import OpenAPICommonCase


class TestOpenAPICommonCase(OpenAPICommonCase):
    def test_openapi(self):
        self._test_openapi()
