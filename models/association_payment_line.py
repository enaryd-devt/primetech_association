# -*- coding: utf-8 -*-

##############################################################################
#
#    PrimeTech Association Management
#    Copyright (C) 2026 PrimeTech Services
#
#    Author: PrimeTech Services
#    License LGPL-3
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AssociationPaymentLine(models.Model):
    _name = "association.payment.line"
    _description = "Ligne d'affectation de paiement"
    _order = "id"

    # ==========================================================
    # TECHNIQUE
    # ==========================================================

    active = fields.Boolean(
        string="Actif",
        default=True,
    )

    sequence = fields.Integer(
        string="Séquence",
        default=10,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Filiale",
        related="payment_id.company_id",
        store=True,
        readonly=True,
        index=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Devise",
        related="payment_id.currency_id",
        store=True,
        readonly=True,
    )

    # ==========================================================
    # PAIEMENT
    # ==========================================================

    payment_id = fields.Many2one(
        comodel_name="association.payment",
        string="Paiement",
        required=True,
        ondelete="cascade",
        index=True,
    )

    payment_date = fields.Date(
        related="payment_id.payment_date",
        string="Date de paiement",
        store=True,
        readonly=True,
    )

    amount_received = fields.Monetary(
        string="Montant reçu",
        currency_field="currency_id",
        default=0.0,
        copy=False,
    )

    # ==========================================================
    # COTISATIONS ÉLIGIBLES
    # ==========================================================

    eligible_subscription_ids = fields.Many2many(
        comodel_name="association.subscription",
        string="Cotisations disponibles",
        compute="_compute_eligible_subscription_ids",
    )


    # ==========================================================
    # COTISATION CHOISIE PAR L'UTILISATEUR
    # ==========================================================

    subscription_id = fields.Many2one(
        comodel_name="association.subscription",
        string="Cotisation",
        ondelete="restrict",
        index=True,
        domain="[('id', 'in', eligible_subscription_ids)]",
    )

    eligible_period_ids = fields.Many2many(
        comodel_name="association.subscription.period",
        string="Cycles disponibles",
        compute="_compute_eligible_period_ids",
    )

    subscription_period_id = fields.Many2one(
        comodel_name="association.subscription.period",
        string="Cycle de cotisation",
        ondelete="restrict",
        index=True,
        domain="[('id', 'in', eligible_period_ids)]",
        help="Cycle non payé ou partiellement payé concerné par cette affectation.",
    )


    # ==========================================================
    # LIGNE TECHNIQUE DU MEMBRE
    # ==========================================================

    subscription_line_id = fields.Many2one(
        comodel_name="association.subscription.line",
        string="Ligne de cotisation",
        ondelete="restrict",
        index=True,
        copy=False,
    )

    member_id = fields.Many2one(
        related="payment_id.member_id",
        string="Membre",
        store=True,
        readonly=True,
    )

    member_code = fields.Char(
        related="payment_id.member_id.member_code",
        string="Code membre",
        store=True,
        readonly=True,
    )

    # ==========================================================
    # MONTANTS
    # ==========================================================

    amount_due = fields.Monetary(
        related="subscription_line_id.amount_due",
        string="Montant dû",
        currency_field="currency_id",
        readonly=True,
    )

    amount_already_paid = fields.Monetary(
        string="Déjà payé",
        currency_field="currency_id",
        compute="_compute_payment_amounts",
    )

    balance_before_payment = fields.Monetary(
        string="Reste avant paiement",
        currency_field="currency_id",
        compute="_compute_payment_amounts",
    )

    amount_paid = fields.Monetary(
        string="Montant affecté",
        currency_field="currency_id",
        required=True,
        default=0.0,
    )

    balance_after_payment = fields.Monetary(
        string="Reste après paiement",
        currency_field="currency_id",
        compute="_compute_payment_amounts",
    )

    # ==========================================================
    # PÉNALITÉ DE RETARD
    # ==========================================================

    is_late = fields.Boolean(
        string="Paiement en retard",
        compute="_compute_penalty_information",
    )

    late_days = fields.Integer(
        string="Jours de retard",
        compute="_compute_penalty_information",
    )

    penalty_amount = fields.Monetary(
        string="Pénalité de retard",
        currency_field="currency_id",
        default=0.0,
    )

    total_with_penalty = fields.Monetary(
        string="Total avec pénalité",
        currency_field="currency_id",
        compute="_compute_total_with_penalty",
    )

    # ==========================================================
    # ÉTAT DE L'AFFECTATION
    # ==========================================================

    allocation_state = fields.Selection(
        selection=[
            ("draft", "À valider"),
            ("partial", "Paiement partiel"),
            ("confirmed", "Affecté"),
            ("cancelled", "Annulé"),
        ],
        string="État de l'affectation",
        compute="_compute_allocation_state",
    )

    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Notes internes",
    )


    # ==========================================================
    # CALCUL DES COTISATIONS ÉLIGIBLES
    # ==========================================================

    @api.depends(
        "payment_id",
        "payment_id.member_id",
        "payment_id.company_id",
    )
    def _compute_eligible_subscription_ids(self):

        SubscriptionLine = self.env[
            "association.subscription.line"
        ]

        Period = self.env[
            "association.subscription.period"
        ]

        for record in self:

            # ======================================================
            # INITIALISATION
            # ======================================================

            record.eligible_subscription_ids = False

            payment = record.payment_id

            if not payment:
                continue

            if not payment.member_id:
                continue

            if not payment.company_id:
                continue

            # ======================================================
            # RECHERCHER UNIQUEMENT LES CYCLES OUVERTS
            # ======================================================

            running_periods = Period.search(
                [
                    (
                        "state",
                        "=",
                        "running",
                    ),
                    (
                        "company_id",
                        "=",
                        payment.company_id.id,
                    ),
                ]
            )

            if not running_periods:
                continue

            # ======================================================
            # COTISATIONS AYANT UN CYCLE OUVERT
            # ======================================================

            running_subscription_ids = (
                running_periods
                .mapped("subscription_id")
                .ids
            )

            if not running_subscription_ids:
                continue

            # ======================================================
            # LIGNES DE COTISATION DU MEMBRE
            #
            # RÈGLE :
            #
            # 1. LE MEMBRE APPARTIENT À LA COTISATION
            # 2. LA COTISATION A UN CYCLE OUVERT
            # 3. MÊME FILIALE
            # ======================================================

            subscription_lines = SubscriptionLine.search(
                [
                    (
                        "member_id",
                        "=",
                        payment.member_id.id,
                    ),
                    (
                        "subscription_id",
                        "in",
                        running_subscription_ids,
                    ),
                    (
                        "subscription_id.company_id",
                        "=",
                        payment.company_id.id,
                    ),
                ]
            )

            if not subscription_lines:
                continue

            # ======================================================
            # EXCLURE LES COTISATIONS DÉJÀ CHOISIES
            # DANS LE MÊME PAIEMENT
            # ======================================================

            selected_subscription_ids = (
                payment.line_ids
                .filtered(
                    lambda line: (
                        line != record
                        and line.subscription_id
                    )
                )
                .mapped("subscription_id")
                .ids
            )

            eligible_lines = subscription_lines.filtered(
                lambda line: (
                    line.subscription_id.id not in selected_subscription_ids
                    and line.payment_state in ("not_paid", "partial")
                    and (line.balance or 0.0) > 0.0
                )
            )

            # ======================================================
            # RÉSULTAT
            # ======================================================

            record.eligible_subscription_ids = (
                eligible_lines.mapped(
                    "subscription_id"
                )
            )
    # ==========================================================
    # RÉSOLUTION DE LA LIGNE DE COTISATION
    # ==========================================================

    @api.depends(
        "subscription_id",
        "payment_id.member_id",
        "payment_id.company_id",
        "subscription_line_id",
        "subscription_line_id.payment_line_ids.amount_paid",
        "subscription_line_id.payment_line_ids.payment_id.state",
        "subscription_line_id.payment_line_ids.subscription_period_id",
    )
    def _compute_eligible_period_ids(self):
        """Offer open cycles whose balance is not settled for this member."""
        Period = self.env["association.subscription.period"]
        PaymentLine = self.env["association.payment.line"]
        for record in self:
            record.eligible_period_ids = False
            if not record.subscription_id or not record.payment_id.member_id:
                continue
            periods = Period.search([
                ("subscription_id", "=", record.subscription_id.id),
                ("company_id", "=", record.payment_id.company_id.id),
                ("state", "=", "running"),
            ])
            available = Period
            subscription_line = record.subscription_line_id
            if not subscription_line:
                subscription_line = self.env["association.subscription.line"].search([
                    ("subscription_id", "=", record.subscription_id.id),
                    ("member_id", "=", record.payment_id.member_id.id),
                ], limit=1)
            for period in periods:
                paid = sum(PaymentLine.search([
                    ("subscription_line_id", "=", subscription_line.id),
                    ("subscription_period_id", "=", period.id),
                    ("payment_id.state", "=", "confirmed"),
                ]).mapped("amount_paid")) if subscription_line else 0.0
                if paid < (record.subscription_id.amount or 0.0):
                    available |= period
            record.eligible_period_ids = available

    def _resolve_subscription_line(self):

        SubscriptionLine = self.env[
            "association.subscription.line"
        ]

        for record in self:

            if not record.subscription_id:
                record.subscription_line_id = False
                continue

            if not record.payment_id.member_id:
                record.subscription_line_id = False
                continue

            subscription_line = SubscriptionLine.search(
                [
                    (
                        "subscription_id",
                        "=",
                        record.subscription_id.id,
                    ),
                    (
                        "member_id",
                        "=",
                        record.payment_id.member_id.id,
                    ),
                    (
                        "company_id",
                        "=",
                        record.payment_id.company_id.id,
                    ),
                ],
                limit=1,
            )

            if not subscription_line:
                raise ValidationError(
                    _(
                        "Le membre %(member)s n'est pas inscrit "
                        "à la cotisation %(subscription)s."
                    )
                    % {
                        "member":
                            record.payment_id.member_id.display_name,

                        "subscription":
                            record.subscription_id.display_name,
                    }
                )

            record.subscription_line_id = (
                subscription_line
            )

            if (
                record.subscription_period_id
                and record.subscription_period_id.subscription_id
                != record.subscription_id
            ):
                raise ValidationError(_("Le cycle sélectionné ne correspond pas à la cotisation."))

            if not record.subscription_period_id:
                record.subscription_period_id = self.env[
                    "association.subscription.period"
                ].search([
                    ("subscription_id", "=", record.subscription_id.id),
                    ("state", "=", "running"),
                    ("company_id", "=", record.payment_id.company_id.id),
                ], order="sequence desc, id desc", limit=1)

        return True


    @api.model_create_multi
    def create(self, vals_list):

        records = super().create(vals_list)

        records._resolve_subscription_line()

        return records


    def write(self, vals):

        result = super().write(vals)

        if (
            "subscription_id" in vals
            or "payment_id" in vals
        ):
            self._resolve_subscription_line()

        return result
    
    # ==========================================================
    # ONCHANGE - COTISATION
    # ==========================================================

    @api.onchange("subscription_id")
    def _onchange_subscription_id(self):

        SubscriptionLine = self.env[
            "association.subscription.line"
        ]

        Period = self.env[
            "association.subscription.period"
        ]

        for record in self:

            # ======================================================
            # RÉINITIALISATION
            # ======================================================

            record.subscription_line_id = False
            record.subscription_period_id = False
            record.amount_paid = 0.0

            if not record.subscription_id:
                continue

            payment = record.payment_id

            if not payment:
                continue

            if not payment.member_id:
                continue

            # ======================================================
            # CONTRÔLER LE CYCLE OUVERT
            # ======================================================

            running_period = Period.search(
                [
                    (
                        "subscription_id",
                        "=",
                        record.subscription_id.id,
                    ),
                    (
                        "state",
                        "=",
                        "running",
                    ),
                    (
                        "company_id",
                        "=",
                        payment.company_id.id,
                    ),
                ],
                order="sequence desc, id desc",
                limit=1,
            )

            if not running_period:

                subscription_name = (
                    record.subscription_id.display_name
                )

                record.subscription_id = False

                return {
                    "warning": {
                        "title":
                            _("Cycle fermé"),

                        "message":
                            _(
                                "La cotisation %(subscription)s "
                                "ne possède aucun cycle ouvert."
                            )
                            % {
                                "subscription":
                                    subscription_name,
                            },
                    }
                }

            # ======================================================
            # RECHERCHER LA LIGNE DU MEMBRE
            # ======================================================

            subscription_line = SubscriptionLine.search(
                [
                    (
                        "subscription_id",
                        "=",
                        record.subscription_id.id,
                    ),
                    (
                        "member_id",
                        "=",
                        payment.member_id.id,
                    ),
                    (
                        "subscription_id.company_id",
                        "=",
                        payment.company_id.id,
                    ),
                ],
                limit=1,
            )

            if not subscription_line:

                subscription_name = (
                    record.subscription_id.display_name
                )

                member_name = (
                    payment.member_id.display_name
                )

                record.subscription_id = False

                return {
                    "warning": {
                        "title":
                            _("Membre non inscrit"),

                        "message":
                            _(
                                "Le membre %(member)s "
                                "n'appartient pas à la cotisation "
                                "%(subscription)s."
                            )
                            % {
                                "member":
                                    member_name,

                                "subscription":
                                    subscription_name,
                            },
                    }
                }

            # ======================================================
            # LIEN TECHNIQUE
            # ======================================================

            record.subscription_line_id = (
                subscription_line
            )
            record.subscription_period_id = running_period

            # ======================================================
            # MONTANT RESTANT DU CYCLE COURANT
            # ======================================================

            confirmed_lines = (
                subscription_line.payment_line_ids.filtered(
                    lambda payment_line: (
                        payment_line.payment_id
                        and
                        payment_line.payment_id.state
                        == "confirmed"
                        and
                        payment_line.payment_id.payment_date
                        and
                        running_period.period_start_date
                        <= payment_line.payment_id.payment_date
                        <= running_period.period_end_date
                    )
                )
            )

            already_paid = sum(
                confirmed_lines.mapped(
                    "amount_paid"
                )
            )

            amount_due = (
                record.subscription_id.amount
                or 0.0
            )

            balance = max(
                amount_due - already_paid,
                0.0,
            )

            # ======================================================
            # MONTANT DISPONIBLE SUR LE PAIEMENT
            # ======================================================

            other_allocations = sum(
                payment.line_ids
                .filtered(
                    lambda line: line != record
                )
                .mapped("amount_paid")
            )

            available_amount = max(
                (
                    payment.amount or 0.0
                )
                - other_allocations,
                0.0,
            )

            # ======================================================
            # AFFECTATION AUTOMATIQUE
            # ======================================================

            record.amount_paid = min(
                balance,
                available_amount,
            )
    
    # ==========================================================
    # CALCUL DES MONTANTS DE L'AFFECTATION
    # ==========================================================

    @api.depends(
        "subscription_line_id",
        "subscription_line_id.amount_due",
        "subscription_line_id.payment_line_ids.amount_paid",
        "subscription_line_id.payment_line_ids.payment_id.state",
        "amount_paid",
        "payment_id.state",
        "subscription_period_id",
    )
    def _compute_payment_amounts(self):

        for record in self:

            # ======================================================
            # INITIALISATION OBLIGATOIRE
            # ======================================================

            record.amount_already_paid = 0.0
            record.balance_before_payment = 0.0
            record.balance_after_payment = 0.0

            # ======================================================
            # PAS ENCORE DE LIGNE TECHNIQUE
            # ======================================================

            if not record.subscription_line_id:
                continue

            subscription_line = record.subscription_line_id

            # ======================================================
            # MONTANT DÛ DU CYCLE COURANT
            # ======================================================

            amount_due = (
                subscription_line.amount_due
                or 0.0
            )

            # ======================================================
            # PAIEMENTS DÉJÀ CONFIRMÉS
            # ======================================================

            confirmed_lines = (
                subscription_line.payment_line_ids.filtered(
                    lambda line: (
                        line.payment_id.state == "confirmed"
                        and line != record
                        and line.subscription_period_id
                        == record.subscription_period_id
                    )
                )
            )

            amount_already_paid = sum(
                confirmed_lines.mapped("amount_paid")
            )

            # ======================================================
            # RESTE AVANT LE PAIEMENT COURANT
            # ======================================================

            balance_before = max(
                amount_due - amount_already_paid,
                0.0,
            )

            # ======================================================
            # MONTANT DE LA LIGNE COURANTE
            # ======================================================

            current_amount = (
                record.amount_paid
                or 0.0
            )

            # ======================================================
            # AFFECTATION
            # ======================================================

            record.amount_already_paid = (
                amount_already_paid
            )

            record.balance_before_payment = (
                balance_before
            )

            record.balance_after_payment = max(
                balance_before - current_amount,
                0.0,
            )

    # ==========================================================
    # COTISATIONS ÉLIGIBLES À L'AFFECTATION
    # ==========================================================

    @api.depends(
        "payment_id",
        "payment_id.member_id",
        "payment_id.company_id",
        "payment_id.line_ids",
        "payment_id.line_ids.subscription_line_id",
    )
    def _compute_eligible_subscription_line_ids(self):

        SubscriptionLine = self.env[
            "association.subscription.line"
        ]

        for record in self:

            # ======================================================
            # INITIALISATION
            # ======================================================

            record.eligible_subscription_line_ids = False

            payment = record.payment_id

            if not payment or not payment.member_id:
                continue

            # ======================================================
            # RECHERCHE DES COTISATIONS DU MEMBRE
            # ======================================================

            subscription_lines = SubscriptionLine.search([
                (
                    "member_id",
                    "=",
                    payment.member_id.id,
                ),
                (
                    "company_id",
                    "=",
                    payment.company_id.id,
                ),
            ])

            # ======================================================
            # FORCER LE RECALCUL DE LA SITUATION DU CYCLE COURANT
            # ======================================================

            if subscription_lines:

                subscription_lines.invalidate_recordset([
                    "amount_due",
                    "amount_paid",
                    "balance",
                    "payment_state",
                ])

            # ======================================================
            # CONSERVER UNIQUEMENT LES IMPAYÉES / PARTIELLES
            # ======================================================

            eligible_lines = subscription_lines.filtered(
                lambda line: (
                    line.subscription_id
                    and line.subscription_id.current_period_id
                    and line.payment_state in (
                        "not_paid",
                        "partial",
                    )
                    and (line.balance or 0.0) > 0.0
                )
            )

            # ======================================================
            # EXCLURE LES COTISATIONS DÉJÀ AJOUTÉES AU PAIEMENT
            # ======================================================

            already_selected_ids = (
                payment.line_ids
                .filtered(
                    lambda line:
                        line != record
                        and line.subscription_line_id
                )
                .mapped("subscription_line_id")
                .ids
            )

            eligible_lines = eligible_lines.filtered(
                lambda line:
                    line.id not in already_selected_ids
            )

            # ======================================================
            # RÉSULTAT
            # ======================================================

            record.eligible_subscription_line_ids = (
                eligible_lines
            )
    
    
    
    # ==========================================================
    # CALCUL DU RETARD ET DE LA PÉNALITÉ
    # ==========================================================

    @api.depends(
        "payment_id.payment_date",
        "payment_id.state",
        "subscription_period_id",
        "subscription_line_id",
        "subscription_line_id.subscription_id",
        "subscription_line_id.subscription_id.period_ids",
        "subscription_line_id.subscription_id.period_ids.state",
        "subscription_line_id.subscription_id.period_ids.due_date",
        "subscription_line_id.subscription_id.period_ids.sequence",
        "amount_paid",
    )
    def _compute_penalty_information(self):

        for record in self:

            # ======================================================
            # INITIALISATION OBLIGATOIRE DE TOUS LES CHAMPS COMPUTE
            # ======================================================

            record.is_late = False
            record.late_days = 0
            record.penalty_amount = 0.0

            # ======================================================
            # LIGNE DE COTISATION
            # ======================================================

            subscription_line = (
                record.subscription_line_id
            )

            if not subscription_line:
                continue

            # ======================================================
            # COTISATION
            # ======================================================

            subscription = (
                subscription_line.subscription_id
            )

            if not subscription:
                continue

            # ======================================================
            # DATE DU PAIEMENT
            # ======================================================

            payment_date = (
                record.payment_id.payment_date
                or fields.Date.context_today(record)
            )

            # ======================================================
            # CYCLE EXPLICITEMENT LIÉ AU PAIEMENT
            # ======================================================

            period = record.subscription_period_id

            # ======================================================
            # COMPATIBILITÉ AVEC LES ANCIENS PAIEMENTS
            # ======================================================

            if not period:

                periods = subscription.period_ids.filtered(
                    lambda item: (
                        item.state in (
                            "running",
                            "closed",
                        )
                        and item.period_start_date
                        and item.period_end_date
                        and item.period_start_date
                        <= payment_date
                        <= item.period_end_date
                    )
                )

                # ==================================================
                # SI AUCUN CYCLE PAR DATE
                # PRENDRE LE CYCLE EN COURS
                # ==================================================

                if not periods:

                    periods = (
                        subscription.period_ids.filtered(
                            lambda item:
                                item.state == "running"
                        )
                    )

                if not periods:
                    continue

                period = periods.sorted(
                    key=lambda item: (
                        item.sequence,
                        item.id,
                    ),
                    reverse=True,
                )[0]

            # ======================================================
            # DATE D'ÉCHÉANCE
            # ======================================================

            due_date = period.due_date

            if not due_date:
                continue

            # ======================================================
            # CALCUL DU NOMBRE DE JOURS DE RETARD
            # ======================================================

            late_days = max(
                (
                    payment_date - due_date
                ).days,
                0,
            )

            record.late_days = late_days

            # ======================================================
            # ÉTAT DU RETARD
            # ======================================================

            record.is_late = bool(
                late_days > 0
            )

            if not record.is_late:
                continue

            # ======================================================
            # CALCUL DE LA PÉNALITÉ
            # ======================================================

            penalty_amount = 0.0

            # ------------------------------------------------------
            # PÉNALITÉ FIXE
            # ------------------------------------------------------

            if (
                hasattr(
                    subscription,
                    "penalty_type",
                )
                and subscription.penalty_type == "fixed"
            ):

                penalty_amount = (
                    subscription.penalty_amount
                    or 0.0
                )

            # ------------------------------------------------------
            # PÉNALITÉ EN POURCENTAGE
            # ------------------------------------------------------

            elif (
                hasattr(
                    subscription,
                    "penalty_type",
                )
                and subscription.penalty_type
                == "percentage"
            ):

                penalty_rate = (
                    subscription.penalty_rate
                    or 0.0
                )

                penalty_amount = (
                    (record.amount_paid or 0.0)
                    * penalty_rate
                    / 100.0
                )

            # ======================================================
            # AFFECTATION DE LA PÉNALITÉ
            # ======================================================

            record.penalty_amount = (
                penalty_amount
            )
    
    # ==========================================================
    # TOTAL AVEC PÉNALITÉ
    # ==========================================================

    @api.depends(
        "amount_paid",
        "penalty_amount",
    )
    def _compute_total_with_penalty(self):
        for record in self:
            record.total_with_penalty = (
                (record.amount_paid or 0.0)
                + (record.penalty_amount or 0.0)
            )

    # ==========================================================
    # ÉTAT DE L'AFFECTATION
    # ==========================================================

    @api.depends(
        "payment_id.state",
        "amount_paid",
        "balance_after_payment",
    )
    def _compute_allocation_state(self):
        for record in self:

            if record.payment_id.state == "cancelled":

                record.allocation_state = "cancelled"

            elif record.payment_id.state != "confirmed":

                record.allocation_state = "draft"

            elif record.balance_after_payment > 0:

                record.allocation_state = "partial"

            else:

                record.allocation_state = "confirmed"

    # ==========================================================
    # ONCHANGE - COTISATION À RÉGLER
    # ==========================================================

    @api.onchange("subscription_line_id")
    def _onchange_subscription_line_id(self):

        for record in self:

            # ======================================================
            # RÉINITIALISATION
            # ======================================================

            record.amount_paid = 0.0

            if not record.subscription_line_id:
                continue

            # ======================================================
            # RESTE À PAYER SUR LA COTISATION
            # ======================================================

            balance = (
                record.balance_before_payment
                or record.subscription_line_id.balance
                or 0.0
            )

            # ======================================================
            # MONTANT ENCORE DISPONIBLE SUR LE PAIEMENT
            # ======================================================

            payment = record.payment_id

            if not payment:
                continue

            other_allocations = sum(
                payment.line_ids
                .filtered(
                    lambda line:
                        line != record
                )
                .mapped("amount_paid")
            )

            available_amount = max(
                (payment.amount or 0.0)
                - other_allocations,
                0.0,
            )

            # ======================================================
            # AFFECTATION AUTOMATIQUE
            # ======================================================

            record.amount_paid = min(
                balance,
                available_amount,
            )
    
    # ==========================================================
    # CONTRAINTES
    # ==========================================================

    @api.constrains(
        "amount_paid",
        "penalty_amount",
    )
    def _check_amounts(self):
        for record in self:

            if record.amount_paid < 0:
                raise ValidationError(
                    _(
                        "Le montant affecté ne peut pas "
                        "être négatif."
                    )
                )

            if record.penalty_amount < 0:
                raise ValidationError(
                    _(
                        "La pénalité de retard ne peut pas "
                        "être négative."
                    )
                )


    # ==========================================================
    # CONTRÔLE FILIALE
    # ==========================================================

    @api.constrains(
        "payment_id",
        "subscription_line_id",
    )
    def _check_company(self):
        for record in self:

            if (
                record.payment_id
                and record.subscription_line_id
                and record.payment_id.company_id
                != record.subscription_line_id.company_id
            ):
                raise ValidationError(
                    _(
                        "Le paiement et la cotisation doivent "
                        "appartenir à la même Filiale."
                    )
                )
            
    # ==========================================================
    # PROTECTION DE SUPPRESSION
    # ==========================================================

    def unlink(self):
        for record in self:

            if (
                record.payment_id
                and record.payment_id.state == "confirmed"
            ):
                raise ValidationError(
                    _(
                        "Impossible de supprimer cette ligne.\n\n"
                        "Le paiement est déjà confirmé et le montant "
                        "a été affecté à la cotisation.\n\n"
                        "Vous devez d'abord annuler le paiement."
                    )
                )

        return super().unlink()
