from .test_checkout_base import CheckoutCommonCase


class CheckoutLisStockPickingCase(CheckoutCommonCase):
    def test_list_stock_picking(self):
        picking1 = self._create_picking()
        picking2 = self._create_picking()
        # should not be in the list because another type:
        picking3 = self._create_picking(picking_type=self.wh.pick_type_id)
        # should not be in list because not assigned:
        self._create_picking()
        to_assign = picking1 | picking2 | picking3
        self._fill_stock_for_moves(to_assign.move_lines, in_package=True)
        to_assign.action_assign()
        response = self.service.dispatch("list_stock_picking", params={})
        expected = {
            "pickings": [
                {
                    "id": picking2.id,
                    "line_count": len(picking2.move_line_ids),
                    "name": picking2.name,
                    "note": "",
                    "origin": "",
                    "partner": {"id": self.customer.id, "name": self.customer.name},
                },
                {
                    "id": picking1.id,
                    "line_count": len(picking1.move_line_ids),
                    "name": picking1.name,
                    "note": "",
                    "origin": "",
                    "partner": {"id": self.customer.id, "name": self.customer.name},
                },
            ]
        }

        self.assert_response(response, next_state="manual_selection", data=expected)
