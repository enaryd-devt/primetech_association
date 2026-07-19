# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MemberAccountSubscriptionPaymentWizard(models.TransientModel):
    _name = "association.member.account.subscription.payment.wizard"
    _description = "Confirmation paiement cotisation depuis compte membre"

    subscription_line_id = fields.Many2one(
        "association.subscription.line", required=True, readonly=True,
        ondelete="cascade", string="Cotisation du membre",
    )
    member_id = fields.Many2one(related="subscription_line_id.member_id", readonly=True)
    currency_id = fields.Many2one(related="subscription_line_id.currency_id", readonly=True)
    amount_due = fields.Monetary(related="subscription_line_id.balance", currency_field="currency_id", readonly=True)
    account_balance = fields.Monetary(
        compute="_compute_account_balance", currency_field="currency_id", readonly=True,
    )
    amount_to_pay = fields.Monetary(
        compute="_compute_account_balance", currency_field="currency_id", readonly=True,
    )

    @api.depends("subscription_line_id", "subscription_line_id.member_id")
    def _compute_account_balance(self):
        Account = self.env["association.member.account"]
        for wizard in self:
            account = Account.search([
                ("member_id", "=", wizard.member_id.id),
                ("company_id", "=", wizard.subscription_line_id.company_id.id),
                ("active", "=", True),
            ], limit=1)
            wizard.account_balance = account.balance if account else 0.0
            wizard.amount_to_pay = min(
                wizard.account_balance or 0.0,
                wizard.amount_due or 0.0,
            )

    def action_confirm(self):
        self.ensure_one()
        if self.amount_to_pay <= 0:
            raise ValidationError(_("Le compte membre ne dispose d'aucun solde utilisable."))
        return self.subscription_line_id.with_context(
            skip_member_account_confirmation=True,
        ).action_pay_from_member_account()
