from .test_checkout_base import CheckoutCommonCase


class CheckoutSummaryCase(CheckoutCommonCase):
    def test_summary_ok(self):
        picking = self._create_picking(
            lines=[
                (self.product_a, 10),
                (self.product_b, 10),
                (self.product_c, 10),
                (self.product_d, 10),
            ]
        )
        response = self.service.dispatch("summary", params={"picking_id": picking.id})

        self.assert_response(
            response,
            next_state="summary",
            data={"picking": self._stock_picking_data(picking)},
        )
