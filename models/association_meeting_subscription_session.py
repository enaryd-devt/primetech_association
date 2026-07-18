# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AssociationMeetingSubscriptionSession(models.Model):
    """A single subscription cycle handled during a meeting.

    A meeting may contain several of these sessions, but a subscription cycle
    can only be handled once in that meeting.  This keeps cash collection,
    settlement and the audit trail isolated from the other subscriptions.
    """

    _name = "association.meeting.subscription.session"
    _description = "Session de cotisation en réunion"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    meeting_id = fields.Many2one(
        "association.meeting", required=True, ondelete="cascade", index=True,
        string="Réunion", tracking=True,
    )
    company_id = fields.Many2one(
        related="meeting_id.company_id", store=True, readonly=True,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id", readonly=True,
    )
    subscription_id = fields.Many2one(
        "association.subscription", required=True, ondelete="restrict",
        string="Cotisation", tracking=True, index=True,
    )
    period_id = fields.Many2one(
        "association.subscription.period", required=True, ondelete="restrict",
        string="Cycle de cotisation", tracking=True, index=True,
        domain="[('subscription_id', '=', subscription_id), ('state', '=', 'running')]",
    )
    state = fields.Selection([
        ("draft", "Brouillon"),
        ("collecting", "En encaissement"),
        ("decision", "En décision de clôture"),
        ("closed", "Clôturée"),
        ("cancelled", "Annulée"),
    ], default="draft", required=True, tracking=True, index=True)
    collection_ids = fields.One2many(
        "association.meeting.collection", "session_id", string="Encaissements",
    )
    payment_ids = fields.One2many(
        "association.payment", "meeting_subscription_session_id",
        string="Paiements", readonly=True,
    )
    allocation_ids = fields.One2many(
        "association.subscription.allocation", "meeting_subscription_session_id",
        string="Bénéficiaires", readonly=True,
    )
    collected_amount = fields.Monetary(
        compute="_compute_statistics", currency_field="currency_id", string="Collecté",
    )
    pending_count = fields.Integer(compute="_compute_statistics", string="En attente")
    paid_count = fields.Integer(compute="_compute_statistics", string="Payés")
    closed_by_id = fields.Many2one("res.users", readonly=True, copy=False)
    closed_at = fields.Datetime(readonly=True, copy=False)
    closure_note = fields.Text(string="Décision de clôture", readonly=True, copy=False)

    _sql_constraints = [
        (
            "meeting_subscription_period_unique",
            "unique(meeting_id, subscription_id, period_id)",
            "Cette cotisation et ce cycle sont déjà traités dans cette réunion.",
        ),
    ]

    @api.constrains("subscription_id", "period_id", "meeting_id")
    def _check_session_values(self):
        for session in self:
            if session.period_id.subscription_id != session.subscription_id:
                raise ValidationError(
                    _("Le cycle sélectionné ne correspond pas à la cotisation.")
                )
            if session.period_id.company_id != session.meeting_id.company_id:
                raise ValidationError(
                    _("Le cycle et la réunion doivent appartenir à la même filiale.")
                )

    @api.depends("collection_ids.state", "collection_ids.payment_id.amount")
    def _compute_statistics(self):
        for session in self:
            paid_lines = session.collection_ids.filtered(
                lambda line: line.state == "paid"
            )
            session.pending_count = len(session.collection_ids.filtered(
                lambda line: line.state == "pending"
            ))
            session.paid_count = len(paid_lines)
            session.collected_amount = sum(paid_lines.mapped("payment_id.amount"))

    def action_start_collection(self):
        for session in self:
            if session.meeting_id.state == "closed":
                raise UserError(_("La réunion est déjà clôturée."))
            if session.period_id.state != "running":
                raise ValidationError(_("Seul un cycle en cours peut être encaissé."))
            if session.state == "draft":
                session.state = "collecting"
        return True

    def action_generate_members(self):
        Collection = self.env["association.meeting.collection"]
        for session in self:
            if session.state not in ("draft", "collecting"):
                raise UserError(_("La session n'est plus ouverte aux encaissements."))
            session.action_start_collection()
            lines = self.env["association.subscription.line"].search([
                ("subscription_id", "=", session.subscription_id.id),
                ("balance", ">", 0),
                ("active", "=", True),
            ], order="member_id")
            existing_ids = set(session.collection_ids.mapped("subscription_line_id").ids)
            values = []
            sequence = max(session.collection_ids.mapped("sequence"), default=0) + 10
            for line in lines:
                if line.id not in existing_ids:
                    values.append({
                        "meeting_id": session.meeting_id.id,
                        "session_id": session.id,
                        "subscription_id": session.subscription_id.id,
                        "subscription_line_id": line.id,
                        "sequence": sequence,
                    })
                    sequence += 10
            if not values:
                raise UserError(_("Aucun membre en attente de paiement n'a été trouvé."))
            Collection.create(values)
        return True

    def action_collect_all(self):
        for session in self:
            if session.state != "collecting":
                raise UserError(_("La session doit être en encaissement."))
            lines = session.collection_ids.filtered(
                lambda line: line.state == "pending" and line.amount > 0
            )
            if not lines:
                raise UserError(_("Saisissez au moins un montant à encaisser."))
            lines.action_collect()
        return True

    def action_open_settlement(self):
        self.ensure_one()
        if self.state not in ("collecting", "decision"):
            raise UserError(_("La session ne peut pas être clôturée dans son état actuel."))
        if self.pending_count:
            raise ValidationError(_("Validez ou annulez tous les encaissements en attente."))
        if self.period_id.state != "running":
            raise ValidationError(_("Le cycle de cotisation n'est plus en cours."))
        self.state = "decision"
        action = self.period_id.action_close()
        action["context"] = dict(
            self.env.context,
            default_meeting_subscription_session_id=self.id,
        )
        return action

    def action_mark_closed(self):
        for session in self:
            session.write({
                "state": "closed",
                "closed_by_id": self.env.user.id,
                "closed_at": fields.Datetime.now(),
            })
        return True

    def action_print_report(self):
        self.ensure_one()
        if self.state != "closed":
            raise UserError(_("Le rapport définitif est disponible après la clôture."))
        return self.env.ref(
            "primetech_association.action_report_meeting_subscription_session"
        ).report_action(self)

    def write(self, vals):
        protected_fields = set(vals) - {"message_follower_ids", "message_ids"}
        if protected_fields:
            for session in self:
                if session.state == "closed" and vals.get("state") != "closed":
                    raise UserError(
                        _("Une session clôturée est verrouillée et ne peut plus être modifiée.")
                    )
        return super().write(vals)
