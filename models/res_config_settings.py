# -*- coding: utf-8 -*-

##############################################################################
#
#    PrimeTech Association Management
#
##############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    association_name = fields.Char(
        string="Association Name",
        config_parameter="primetech_association.association_name",
    )

    membership_prefix = fields.Char(
        string="Membership Number Prefix",
        default="MEM",
        config_parameter="primetech_association.membership_prefix",
    )

    membership_card_validity = fields.Integer(
        string="Membership Card Validity (Months)",
        default=12,
        config_parameter="primetech_association.membership_card_validity",
    )

    default_subscription_amount = fields.Float(
        string="Default Subscription Amount",
        default=0.0,
        config_parameter="primetech_association.default_subscription_amount",
    )

    allow_partial_payment = fields.Boolean(
        string="Allow Partial Payments",
        default=True,
        config_parameter="primetech_association.allow_partial_payment",
    )

    require_member_photo = fields.Boolean(
        string="Require Member Photo",
        default=False,
        config_parameter="primetech_association.require_member_photo",
    )

    automatic_member_number = fields.Boolean(
        string="Automatic Member Number",
        default=True,
        config_parameter="primetech_association.automatic_member_number",
    )