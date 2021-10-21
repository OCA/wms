# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from .common import CommonCase


class ProfileCase(CommonCase):
    def setUp(self):
        super().setUp()
        with self.work_on_services() as work:
            self.service = work.component(usage="profile")

    def test_profile_search(self):
        """Request /profile/search"""
        # Simulate the client searching profiles
        response = self.service.dispatch("search")
        self.assert_response(
            response,
            data={
                "size": 2,
                "records": [
                    {"id": self.ANY, "name": "Demo Profile 1"},
                    {"id": self.ANY, "name": "Demo Profile 2"},
                ],
            },
        )
