# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from .common import CommonCase


class ProfileCase(CommonCase):
    def test_profile_search(self):
        """Request /profile/search"""
        service = self.get_service("profile")
        # Simulate the client searching profiles
        response = service.dispatch("search")
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
