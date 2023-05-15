# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.tools.safe_eval import safe_eval

from odoo.addons.stock_release_channel.tests.common import ReleaseChannelCase


class TestReleaseChannel(ReleaseChannelCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.carrier = cls.env.ref("delivery.free_delivery_carrier")
        cls.channel = cls._create_channel(
            name="Test Domain",
            sequence=1,
            rule_domain=[("priority", "=", "1")],
        )

    def test_basic(self):
        """
        data: the default release channel and one carrier
        case: assign the carrier to the release channel and run the
              _onchange_carrier_id method
        result: the rule_domain is set for carrier
        """
        carrier_term = ("carrier_id.id", "=", self.carrier.id)
        self.assertEqual(safe_eval(self.default_channel.rule_domain), [])
        self.default_channel.carrier_id = self.carrier
        self.default_channel._onchange_carrier_id()
        safe_dom = safe_eval(self.default_channel.rule_domain)
        self.assertEqual(len(safe_dom), 1)
        self.assertEqual(safe_dom[0], carrier_term)

    def test_basic_2(self):
        """
        data: A release channel with a rule_domain and one carrier
        case: assign the carrier to the release channel and run the
              _onchange_carrier_id method
        result: the rule_domain is augmented with a rule for carrier and this rule
                is the first one
        """
        carrier_term = ("carrier_id.id", "=", self.carrier.id)
        self.assertEqual(len(safe_eval(self.channel.rule_domain)), 1)
        self.channel.carrier_id = self.carrier
        self.channel._onchange_carrier_id()
        safe_dom = safe_eval(self.channel.rule_domain)
        self.assertEqual(len(safe_dom), 2)
        self.assertEqual(safe_dom[0], carrier_term)
