# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)

from odoo import http

from odoo.addons.shopfloor_base.controllers import main


class ShopfloorController(main.ShopfloorController):
    @http.route(
        ["/shopfloor/partner_example/scan/<string:identifier>"],
        methods=["GET"],
        auth="api_key",
    )
    def partner_example_scan(self, identifier):
        """Scan a partner ref and return its data.
        """
        return self._process_method("partner_example", "scan", identifier)

    @http.route(
        ["/shopfloor/partner_example/partner_list"], methods=["GET"], auth="api_key"
    )
    def partner_example_partner_list(self, **params):
        """Return list of available partners.
        """
        return self._process_method("partner_example", "partner_list", params=params)

    @http.route(
        ["/shopfloor/partner_example/detail/<int:partner_id>"],
        methods=["GET"],
        auth="api_key",
    )
    def partner_example_detail(self, partner_id):
        """Retrieve full detail for partner ID.
        """
        return self._process_method("partner_example", "detail", partner_id)
