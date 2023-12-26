# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from .common import CommonCase
from .common_misc import OpenAPITestMixin


class TestOpenAPICommonCase(CommonCase, OpenAPITestMixin):
    def test_openapi(self):
        self._test_openapi()
