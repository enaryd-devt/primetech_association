# -*- coding: utf-8 -*-

from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AssociationSubscriptionPeriod(models.Model):
    _name = "association.subscription.period"
    _description = "Cycle de cotisation"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "sequence desc, id desc"
    _rec_name = "name"

    # ==========================================================
    # IDENTIFICATION
    # ==========================================================

    name = fields.Char(
        string="Cycle",
        compute="_compute_name",
        store=True,
    )

    sequence = fields.Integer(
        string="N° cycle",
        required=True,
        default=1,
        index=True,
        tracking=True,
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
    )

    # ==========================================================
    # COTISATION
    # ==========================================================

    subscription_id = fields.Many2one(
        comodel_name="association.subscription",
        string="Cotisation",
        required=True,
        ondelete="cascade",
        index=True,
        tracking=True,
    )

    subscription_type = fields.Selection(
        related="subscription_id.subscription_type",
        string="Type de cotisation",
        store=True,
        readonly=True,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Filiale",
        related="subscription_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Devise",
        related="subscription_id.currency_id",
        store=True,
        readonly=True,
    )

    # ==========================================================
    # PÉRIODE
    # ==========================================================

    period_start_date = fields.Date(
        string="Début du cycle",
        required=True,
        tracking=True,
        index=True,
    )

    period_end_date = fields.Date(
        string="Fin du cycle",
        required=True,
        tracking=True,
        index=True,
    )

    due_date = fields.Date(
        string="Date d'échéance",
        required=True,
        tracking=True,
        index=True,
    )

    # ==========================================================
    # DÉLAI ET PÉNALITÉ
    # ==========================================================

    penalty_deadline = fields.Date(
        string="Date limite avant pénalité",
        compute="_compute_penalty_deadline",
        store=True,
    )

    penalty_amount = fields.Monetary(
        string="Pénalité",
        currency_field="currency_id",
        default=0.0,
        readonly=True,
    )

    penalty_applied = fields.Boolean(
        string="Pénalité appliquée",
        default=False,
        readonly=True,
    )

    penalty_date = fields.Date(
        string="Date d'application de la pénalité",
        readonly=True,
    )

    penalty_reason = fields.Char(
        string="Motif de la pénalité",
        readonly=True,
    )

    # ==========================================================
    # ÉTAT
    # ==========================================================

    state = fields.Selection(
        selection=[
            ("draft", "Brouillon"),
            ("running", "En cours"),
            ("closed", "Terminé"),
            ("cancelled", "Annulé"),
        ],
        string="Statut",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    # ==========================================================
    # CAGNOTTE
    # ==========================================================

    allocation_ids = fields.One2many(
        comodel_name="association.subscription.allocation",
        inverse_name="period_id",
        string="Bénéficiaires",
    )

    collected_amount = fields.Monetary(
        string="Cagnotte collectée",
        compute="_compute_pot_statistics",
        currency_field="currency_id",
    )

    allocated_amount = fields.Monetary(
        string="Montant attribué",
        compute="_compute_pot_statistics",
        currency_field="currency_id",
    )

    available_amount = fields.Monetary(
        string="Cagnotte disponible",
        compute="_compute_pot_statistics",
        currency_field="currency_id",
    )

    beneficiary_count = fields.Integer(
        string="Bénéficiaires",
        compute="_compute_pot_statistics",
    )

    # ==========================================================
    # STATISTIQUES MEMBRES
    # ==========================================================

    member_count = fields.Integer(
        string="Membres",
        compute="_compute_member_statistics",
    )

    paid_member_count = fields.Integer(
        string="Payés",
        compute="_compute_member_statistics",
    )

    partial_member_count = fields.Integer(
        string="Partiels",
        compute="_compute_member_statistics",
    )

    unpaid_member_count = fields.Integer(
        string="Non payés",
        compute="_compute_member_statistics",
    )

    expected_amount = fields.Monetary(
        string="Montant attendu",
        compute="_compute_member_statistics",
        currency_field="currency_id",
    )

    recovery_rate = fields.Float(
        string="Taux de recouvrement",
        compute="_compute_member_statistics",
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Notes internes",
    )

    # ==========================================================
    # CONTRAINTES SQL
    # ==========================================================

    _sql_constraints = [
        (
            "association_subscription_period_sequence_unique",
            "unique(subscription_id, sequence)",
            "Le numéro du cycle doit être unique pour la cotisation.",
        ),
        (
            "association_subscription_period_dates_unique",
            "unique(subscription_id, period_start_date, period_end_date)",
            "Un cycle existe déjà pour cette période.",
        ),
    ]

    # ==========================================================
    # NOM
    # ==========================================================

    @api.depends(
        "sequence",
        "period_start_date",
        "period_end_date",
    )
    def _compute_name(self):

        for period in self:

            cycle_number = str(
                period.sequence or 0
            ).zfill(3)

            if (
                period.period_start_date
                and period.period_end_date
            ):

                if (
                    period.period_start_date
                    == period.period_end_date
                ):

                    date_label = fields.Date.to_string(
                        period.period_start_date
                    )

                else:

                    date_label = _(
                        "%(start)s au %(end)s"
                    ) % {
                        "start": fields.Date.to_string(
                            period.period_start_date
                        ),
                        "end": fields.Date.to_string(
                            period.period_end_date
                        ),
                    }

                period.name = _(
                    "Cycle %(cycle)s - %(date)s"
                ) % {
                    "cycle": cycle_number,
                    "date": date_label,
                }

            else:

                period.name = _(
                    "Cycle %(cycle)s"
                ) % {
                    "cycle": cycle_number,
                }

    # ==========================================================
    # LIGNES DU CYCLE
    # ==========================================================

    def _get_subscription_lines(self):

        self.ensure_one()

        return self.subscription_id.line_ids.filtered(
            lambda line: line.active
        )

    # ==========================================================
    # CAGNOTTE
    # ==========================================================

    @api.depends(
        "subscription_id.line_ids.amount_paid",
        "subscription_id.line_ids.payment_state",
        "allocation_ids.amount",
        "allocation_ids.state",
    )
    def _compute_pot_statistics(self):

        for period in self:

            lines = period._get_subscription_lines()

            collected_amount = sum(
                lines.mapped("amount_paid")
            )

            allocated_amount = sum(
                period.allocation_ids.filtered(
                    lambda allocation:
                        allocation.state in (
                            "confirmed",
                            "paid",
                        )
                ).mapped("amount")
            )

            period.collected_amount = collected_amount
            period.allocated_amount = allocated_amount
            period.available_amount = max(
                collected_amount - allocated_amount,
                0.0,
            )

            period.beneficiary_count = len(
                period.allocation_ids.filtered(
                    lambda allocation:
                        allocation.state != "cancelled"
                )
            )

    # ==========================================================
    # STATISTIQUES MEMBRES
    # ==========================================================

    @api.depends(
        "subscription_id.line_ids.amount_due",
        "subscription_id.line_ids.amount_paid",
        "subscription_id.line_ids.payment_state",
    )
    def _compute_member_statistics(self):

        for period in self:

            lines = period._get_subscription_lines()

            period.member_count = len(lines)

            period.paid_member_count = len(
                lines.filtered(
                    lambda line:
                        line.payment_state == "paid"
                )
            )

            period.partial_member_count = len(
                lines.filtered(
                    lambda line:
                        line.payment_state == "partial"
                )
            )

            period.unpaid_member_count = len(
                lines.filtered(
                    lambda line:
                        line.payment_state == "not_paid"
                )
            )

            period.expected_amount = sum(
                lines.mapped("amount_due")
            )

            if period.expected_amount > 0:

                period.recovery_rate = (
                    period.collected_amount
                    / period.expected_amount
                ) * 100

            else:

                period.recovery_rate = 0.0

    # ==========================================================
    # CONTRAINTES
    # ==========================================================

    @api.constrains(
        "period_start_date",
        "period_end_date",
        "due_date",
    )
    def _check_period_dates(self):

        for period in self:

            if (
                period.period_end_date
                < period.period_start_date
            ):

                raise ValidationError(
                    _(
                        "La date de fin du cycle ne peut pas "
                        "être antérieure à sa date de début."
                    )
                )

            if (
                period.due_date
                < period.period_start_date
            ):

                raise ValidationError(
                    _(
                        "La date d'échéance ne peut pas être "
                        "antérieure au début du cycle."
                    )
                )

    
    # ==========================================================
    # DATE LIMITE AVANT PÉNALITÉ
    # ==========================================================

    @api.depends(
        "due_date",
        "subscription_id.penalty_grace_days",
    )
    def _compute_penalty_deadline(self):

        for record in self:

            record.penalty_deadline = False

            if not record.due_date:
                continue

            grace_days = (
                record.subscription_id.penalty_grace_days
                or 0
            )

            record.penalty_deadline = (
                record.due_date
                + timedelta(days=grace_days)
            )

    # ==========================================================
    # APPLIQUER LA PÉNALITÉ
    # ==========================================================

    def _apply_late_penalty(self):
        for record in self:
            lines = record._get_subscription_lines()
            lines._apply_late_penalty()
            penalized = lines.filtered("penalty_applied")
            record.write({
                "penalty_amount": sum(penalized.mapped("penalty_amount")),
                "penalty_applied": bool(penalized),
                "penalty_date": max(
                    penalized.mapped("penalty_date"), default=False
                ),
                "penalty_reason": (
                    _("Pénalités calculées selon l'échéance du cycle.")
                    if penalized else False
                ),
            })
        return True

    def action_start(self):

        for period in self:

            if period.state != "draft":

                raise UserError(
                    _(
                        "Seul un cycle en brouillon "
                        "peut être démarré."
                    )
                )

            running_period = self.search(
                [
                    (
                        "subscription_id",
                        "=",
                        period.subscription_id.id,
                    ),
                    (
                        "state",
                        "=",
                        "running",
                    ),
                    (
                        "id",
                        "!=",
                        period.id,
                    ),
                ],
                limit=1,
            )

            if running_period:

                raise ValidationError(
                    _(
                        "Le cycle %(cycle)s est déjà en cours "
                        "pour cette cotisation."
                    )
                    % {
                        "cycle":
                            running_period.display_name,
                    }
                )

            if period.sequence > 1:
                period.subscription_id.line_ids.write({
                    "penalty_amount": 0.0,
                    "penalty_applied": False,
                    "penalty_date": False,
                    "penalty_reason": False,
                })

            period.state = "running"

            period.message_post(
                body=_(
                    "Le cycle %(cycle)s a été démarré."
                )
                % {
                    "cycle": period.display_name,
                }
            )

        return True

    # ==========================================================
    # TERMINER LE CYCLE
    # ==========================================================

    def action_close(self):
        self.ensure_one()

        # ======================================================
        # CONTRÔLE DU STATUT
        # ======================================================

        if self.state != "running":
            raise UserError(
                _(
                    "Seul un cycle en cours "
                    "peut être terminé."
                )
            )

        # ======================================================
        # CONTRÔLE DES ATTRIBUTIONS EN BROUILLON
        # ======================================================

        draft_allocations = self.allocation_ids.filtered(
            lambda allocation:
                allocation.state == "draft"
        )

        if draft_allocations:
            raise ValidationError(
                _(
                    "Le cycle contient %(count)s attribution(s) "
                    "de cagnotte encore en brouillon.\n\n"
                    "Confirmez ou annulez ces attributions "
                    "avant de terminer le cycle."
                )
                % {
                    "count": len(draft_allocations),
                }
            )

        # ======================================================
        # CRÉATION DU WIZARD
        # ======================================================

        wizard = self.env[
            "association.subscription.cycle.close.wizard"
        ].create({
            "period_id": self.id,
        })

        # ======================================================
        # OUVERTURE DU WIZARD
        # ======================================================

        return {
            "type": "ir.actions.act_window",
            "name": _("Clôture du cycle"),
            "res_model":
                "association.subscription.cycle.close.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "view_id": self.env.ref(
                "primetech_association."
                "view_association_subscription_cycle_close_wizard_form"
            ).id,
            "target": "new",
        }
    # ==========================================================
    # ANNULER
    # ==========================================================

    def action_cancel(self):

        for period in self:

            if period.state == "closed":

                raise UserError(
                    _(
                        "Un cycle terminé ne peut pas "
                        "être annulé."
                    )
                )

            confirmed_allocations = (
                period.allocation_ids.filtered(
                    lambda allocation:
                        allocation.state in (
                            "confirmed",
                            "paid",
                        )
                )
            )

            if confirmed_allocations:

                raise ValidationError(
                    _(
                        "Ce cycle possède des attributions "
                        "confirmées ou déjà remises."
                    )
                )

            period.state = "cancelled"

        return True
