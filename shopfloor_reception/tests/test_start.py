# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestStart(CommonCase):
    def test_start(self):
        pickings = self.env["stock.picking"]
        response = self.service.dispatch("start")
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": []},
        )
        # Create a first picking
        pickings |= self._create_picking()
        response = self.service.dispatch("start")
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self.data.pickings(pickings)},
        )
        # And a second one
        pickings |= self._create_picking()
        response = self.service.dispatch("start")
        self.assert_response(
            response,
            next_state="select_document",
            data={"pickings": self.data.pickings(pickings)},
        )
