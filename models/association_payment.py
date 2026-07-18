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
from odoo.exceptions import UserError, ValidationError


class AssociationPayment(models.Model):
    _name = "association.payment"
    _description = "Paiement d'association"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "payment_date desc, id desc"
    _rec_name = "name"

    # ==========================================================
    # TECHNIQUE
    # ==========================================================

    active = fields.Boolean(
        string="Actif",
        default=True,
        tracking=True,
    )

    sequence = fields.Integer(
        string="Séquence",
        default=10,
    )

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Filiale",
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )

    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Devise",
        related="company_id.currency_id",
        readonly=True,
        store=True,
    )

    color = fields.Integer(
        string="Couleur",
    )

    # ==========================================================
    # IDENTIFICATION
    # ==========================================================

    name = fields.Char(
        string="Référence du paiement",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("Nouveau"),
        tracking=True,
        index=True,
    )

    description = fields.Text(
        string="Description",
    )

    # ==========================================================
    # MEMBRE
    # ==========================================================

    member_id = fields.Many2one(
        comodel_name="association.member",
        string="Membre",
        required=True,
        tracking=True,
        ondelete="restrict",
        index=True,
    )

    member_code = fields.Char(
        related="member_id.member_code",
        string="Code membre",
        readonly=True,
        store=True,
    )

    member_image_128 = fields.Image(
        related="member_id.image_128",
        string="Photo du membre",
        readonly=True,
    )

    category_id = fields.Many2one(
        related="member_id.category_id",
        string="Catégorie",
        readonly=True,
        store=True,
    )

    function_id = fields.Many2one(
        related="member_id.function_id",
        string="Fonction",
        readonly=True,
        store=True,
    )

    # ==========================================================
    # PAIEMENT
    # ==========================================================

    payment_date = fields.Date(
        string="Date de paiement",
        default=fields.Date.context_today,
        required=True,
        tracking=True,
        index=True,
    )

    amount = fields.Monetary(
        string="Montant du paiement",
        currency_field="currency_id",
        required=True,
        default=0.0,
        tracking=True,
    )

    allocated_amount = fields.Monetary(
        string="Montant affecté",
        currency_field="currency_id",
        compute="_compute_payment_totals",
    )

    remaining_amount = fields.Monetary(
        string="Montant non affecté",
        currency_field="currency_id",
        compute="_compute_payment_totals",
    )

    payment_method = fields.Selection(
        selection=[
            ("cash", "Espèces"),
            ("bank", "Virement bancaire"),
            ("cheque", "Chèque"),
            ("mobile_money", "Mobile Money"),
            ("other", "Autre"),
        ],
        string="Mode de paiement",
        required=True,
        default="cash",
        tracking=True,
        index=True,
    )

    payment_reference = fields.Char(
        string="Référence externe",
        tracking=True,
        help=(
            "Référence Mobile Money, numéro de chèque, "
            "référence bancaire ou autre référence externe."
        ),
    )

    state = fields.Selection(
        selection=[
            ("draft", "Brouillon"),
            ("collected", "Encaissé"),
            ("confirmed", "Validé"),
            ("cancelled", "Annulé"),
        ],
        string="Statut",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    # ==========================================================
    # LIGNES DE PAIEMENT
    # ==========================================================

    line_ids = fields.One2many(
        comodel_name="association.payment.line",
        inverse_name="payment_id",
        string="Affectations du paiement",
        copy=True,
    )

    line_count = fields.Integer(
        string="Nombre de lignes",
        compute="_compute_payment_totals",
    )


    # ==========================================================
    # CYCLE DE COTISATION
    # ==========================================================

    subscription_period_id = fields.Many2one(
        comodel_name="association.subscription.period",
        string="Cycle de cotisation",
        ondelete="restrict",
        readonly=True,
        copy=False,
        index=True,
    )
    
    # ==========================================================
    # ORIGINE DU PAIEMENT
    # ==========================================================

    payment_source = fields.Selection(
        selection=[
            ("external", "Versement du membre"),
            ("member_account", "Compte membre"),
            (
                "meeting_cash",
                "Caisse temporaire de réunion",
            ),
        ],
        string="Origine du paiement",
        required=True,
        default="external",
        tracking=True,
    )

    meeting_id = fields.Many2one(
        comodel_name="association.meeting",
        string="Réunion d'encaissement",
        readonly=True,
        copy=False,
        ondelete="restrict",
        index=True,
    )

    member_account_id = fields.Many2one(
        comodel_name="association.member.account",
        string="Compte membre",
        domain="[('member_id', '=', member_id)]",
        tracking=True,
    )

    member_account_balance = fields.Monetary(
        string="Solde du compte membre",
        currency_field="currency_id",
        compute="_compute_member_account_balance",
    )

    # ==========================================================
    # COMPTE DE VERSEMENT
    # ==========================================================

    receipt_account_id = fields.Many2one(
        comodel_name="association.fund",
        string="Compte de versement",
        domain="[('active', '=', True), ('company_id', '=', company_id)]",
        tracking=True,
        index=True,
    )

    receipt_account_type = fields.Selection(
        related="receipt_account_id.fund_type",
        string="Type de compte",
        readonly=True,
    )

    receipt_account_balance = fields.Monetary(
        related="receipt_account_id.current_balance",
        string="Solde du compte",
        currency_field="currency_id",
        readonly=True,
    )

    # ==========================================================
    # AFFECTATION
    # ==========================================================

    has_allocations = fields.Boolean(
        string="Affecter à des cotisations",
        default=False,
        tracking=True,
    )

    # ==========================================================
    # SURPLUS
    # ==========================================================

    surplus_processed = fields.Boolean(
        string="Surplus traité",
        default=False,
        copy=False,
    )

    refund_amount = fields.Monetary(
        string="Montant remboursé",
        currency_field="currency_id",
        default=0.0,
        readonly=True,
        copy=False,
    )

    processed_surplus_amount = fields.Monetary(
        string="Surplus traité",
        currency_field="currency_id",
        default=0.0,
        readonly=True,
        copy=False,
    )

    surplus_action = fields.Selection(
        [("member_account", "Crédité au compte membre"),
         ("refund", "Remboursé")],
        string="Destination du surplus",
        readonly=True,
        copy=False,
    )
    # ==========================================================
    # NOTES
    # ==========================================================

    note = fields.Html(
        string="Notes internes",
    )

    # ==========================================================
    # CRÉATION DU MOUVEMENT DU COMPTE DE VERSEMENT
    # ==========================================================

    def _create_receipt_fund_transaction(self):

        Transaction = self.env[
            "association.fund.transaction"
        ]

        for record in self:

            if record.payment_source != "external":
                continue

            if not record.receipt_account_id:
                raise ValidationError(
                    _(
                        "Vous devez sélectionner "
                        "un compte de versement."
                    )
                )

            existing_transaction = Transaction.search(
                [
                    (
                        "payment_id",
                        "=",
                        record.id,
                    ),
                    (
                        "transaction_type",
                        "=",
                        "in",
                    ),
                ],
                limit=1,
            )

            if existing_transaction:
                continue

            amount_to_deposit = record.amount
            if record.surplus_action == "refund":
                amount_to_deposit -= record.processed_surplus_amount

            if amount_to_deposit <= 0:
                continue

            transaction = Transaction.create(
                {
                    "fund_id": record.receipt_account_id.id,
                    "transaction_type": "in",
                    "amount": amount_to_deposit,
                    "transaction_date": record.payment_date,
                    "description": _(
                        "Encaissement paiement %s - %s"
                    )
                    % (
                        record.name,
                        record.member_id.display_name,
                    ),
                    "company_id": record.company_id.id,
                    "payment_id": record.id,
                }
            )

            transaction.action_validate()

        return True

    # ==========================================================
    # SOLDE DU COMPTE MEMBRE
    # ==========================================================

    @api.depends(
        "member_id",
        "member_account_id",
    )
    def _compute_member_account_balance(self):

        for record in self:

            record.member_account_balance = 0.0

            account = record.member_account_id

            if not account and record.member_id:

                account = self.env[
                    "association.member.account"
                ].search(
                    [
                        (
                            "member_id",
                            "=",
                            record.member_id.id,
                        ),
                        (
                            "company_id",
                            "=",
                            record.company_id.id,
                        ),
                    ],
                    limit=1,
                )

            if account:

                record.member_account_balance = (
                    account.balance or 0.0
                )

    # ==========================================================
    # CONTRAINTES SQL
    # ==========================================================

    _sql_constraints = [
        (
            "association_payment_name_company_unique",
            "unique(name, company_id)",
            "La référence du paiement doit être unique par filiale.",
        ),
        (
            "association_payment_amount_positive",
            "CHECK(amount >= 0)",
            "Le montant du paiement ne peut pas être négatif.",
        ),
    ]

    # ==========================================================
    # CALCUL DES TOTAUX
    # ==========================================================

    @api.depends(
        "amount",
        "line_ids",
        "line_ids.amount_paid",
    )
    def _compute_payment_totals(self):

        for record in self:

            allocated_amount = sum(
                record.line_ids.mapped(
                    "amount_paid"
                )
            )

            record.line_count = len(
                record.line_ids
            )

            record.allocated_amount = (
                allocated_amount
            )

            record.remaining_amount = max(
                (record.amount or 0.0)
                - allocated_amount,
                0.0,
            )

    # ==========================================================
    # ONCHANGE - MEMBRE
    # ==========================================================

    @api.onchange("member_id")
    def _onchange_member_id(self):

        for record in self:

            record.line_ids = [
                (5, 0, 0)
            ]

            record.member_account_id = False
            record.receipt_account_id = False

            if not record.member_id:
                continue

            record.company_id = (
                record.member_id.company_id
            )

            account = self.env[
                "association.member.account"
            ].search(
                [
                    (
                        "member_id",
                        "=",
                        record.member_id.id,
                    ),
                    (
                        "company_id",
                        "=",
                        record.member_id.company_id.id,
                    ),
                ],
                limit=1,
            )

            if account:

                record.member_account_id = account


    # ==========================================================
    # ONCHANGE - ORIGINE DU PAIEMENT
    # ==========================================================

    @api.onchange("payment_source")
    def _onchange_payment_source(self):

        for record in self:

            # --------------------------------------------------
            # VERSEMENT EXTERNE
            # --------------------------------------------------

            if record.payment_source == "external":

                record.member_account_id = False

                # L'utilisateur choisira le compte financier
                # qui reçoit réellement le versement.
                record.receipt_account_id = False

                continue

            # --------------------------------------------------
            # COMPTE MEMBRE
            # --------------------------------------------------

            if record.payment_source == "member_account":

                # Aucun compte de trésorerie ne doit être utilisé.
                record.receipt_account_id = False

                # Une cotisation depuis le compte membre
                # doit obligatoirement être affectée.
                record.has_allocations = True

                # Recherche automatique du compte du membre.
                account = False

                if record.member_id:

                    account = self.env[
                        "association.member.account"
                    ].search(
                        [
                            (
                                "member_id",
                                "=",
                                record.member_id.id,
                            ),
                            (
                                "company_id",
                                "=",
                                record.company_id.id,
                            ),
                        ],
                        limit=1,
                    )

                record.member_account_id = account

                continue

            # --------------------------------------------------
            # AUCUNE ORIGINE
            # --------------------------------------------------

            record.receipt_account_id = False
            record.member_account_id = False
            record.has_allocations = False
    # ==========================================================
    # ONCHANGE - AFFECTATIONS
    # ==========================================================

    @api.onchange("has_allocations")
    def _onchange_has_allocations(self):

        for record in self:

            if not record.has_allocations:

                record.line_ids = [
                    (5, 0, 0)
                ]


    # ==========================================================
    # CONTRÔLE DE L'ORIGINE DU PAIEMENT
    # ==========================================================

    def _check_payment_source_values(self):

        for record in self:

            if record.payment_source == "external":

                if not record.receipt_account_id:

                    raise ValidationError(
                        _(
                            "Vous devez sélectionner "
                            "le compte de versement."
                        )
                    )

            elif (
                record.payment_source
                == "member_account"
            ):

                if not record.member_account_id:

                    raise ValidationError(
                        _(
                            "Aucun compte membre "
                            "n'est disponible."
                        )
                    )

                if record.receipt_account_id:

                    raise ValidationError(
                        _(
                            "Un paiement depuis le compte "
                            "membre ne peut pas utiliser "
                            "un compte de trésorerie."
                        )
                    )

                if (
                    record.member_account_id.balance
                    < record.amount
                ):

                    raise ValidationError(
                        _(
                            "Solde du compte membre "
                            "insuffisant.\n\n"
                            "Disponible : %(balance).2f "
                            "%(currency)s"
                        )
                        % {
                            "balance":
                                record.member_account_id.balance,

                            "currency":
                                record.currency_id.name
                                or "",
                        }
                    )

            elif record.payment_source == "meeting_cash":

                if not record.meeting_id:
                    raise ValidationError(
                        _(
                            "Un encaissement temporaire doit être "
                            "rattaché à une réunion."
                        )
                    )

                if record.receipt_account_id:
                    raise ValidationError(
                        _(
                            "La caisse temporaire de réunion ne peut "
                            "pas mouvementer directement un compte "
                            "financier."
                        )
                    )
                
    # ==========================================================
    # DÉBITER LE COMPTE MEMBRE
    # ==========================================================

    def _debit_member_account(self):

        for record in self:

            if (
                record.payment_source
                != "member_account"
            ):
                continue

            account = record.member_account_id

            if not account:

                raise ValidationError(
                    _("Compte membre introuvable.")
                )

            transaction = self.env[
                "association.member.account.transaction"
            ].create(
                {
                    "account_id":
                        account.id,

                    "transaction_type":
                        "debit",

                    "amount":
                        record.amount,

                    "transaction_date":
                        record.payment_date,

                    "description":
                        _(
                            "Paiement %(payment)s"
                        )
                        % {
                            "payment":
                                record.name,
                        },
                }
            )

            if hasattr(
                transaction,
                "action_confirm",
            ):

                transaction.action_confirm()
    
    
    # ==========================================================
    # INVALIDATION DES COTISATIONS ET CYCLES
    # ==========================================================

    def _invalidate_subscription_lines(self):

        # ======================================================
        # LIGNES DE COTISATION
        # ======================================================

        subscription_lines = self.line_ids.mapped(
            "subscription_line_id"
        )

        if subscription_lines:

            subscription_lines.invalidate_recordset([
                "amount_paid",
                "balance",
                "payment_state",
                "payment_date",
            ])

            subscription_lines.modified([
                "amount_paid",
                "balance",
                "payment_state",
                "payment_date",
            ])

        # ======================================================
        # CYCLES DE COTISATION CONCERNÉS
        # ======================================================

        periods = self.env[
            "association.subscription.period"
        ]

        subscriptions = subscription_lines.mapped(
            "subscription_id"
        )

        if subscriptions:

            periods = self.env[
                "association.subscription.period"
            ].search([
                (
                    "subscription_id",
                    "in",
                    subscriptions.ids,
                ),
                (
                    "state",
                    "=",
                    "running",
                ),
            ])

        # ======================================================
        # INVALIDATION DES STATISTIQUES DE CAGNOTTE
        # ======================================================

        if periods:

            period_fields = [
                field_name
                for field_name in (
                    "collected_amount",
                    "allocated_amount",
                    "available_amount",
                    "member_count",
                    "paid_member_count",
                    "partial_member_count",
                    "unpaid_member_count",
                    "recovery_rate",
                    "beneficiary_count",
                )
                if field_name in periods._fields
            ]

            if period_fields:

                periods.invalidate_recordset(
                    period_fields
                )

                periods.modified(
                    period_fields
                )

        return True
    # ==========================================================
    # CREATE
    # ==========================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("Nouveau")) == _("Nouveau"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code(
                        "association.payment"
                    )
                    or _("Nouveau")
                )

        return super().create(vals_list)

    # ==========================================================
    # ONCHANGE MEMBRE
    # ==========================================================

    @api.onchange("member_id")
    def _onchange_member_id(self):
        for record in self:
            if record.member_id:
                record.company_id = record.member_id.company_id

            record.line_ids = [(5, 0, 0)]


    # ==========================================================
    # ONCHANGE
    # ==========================================================

    @api.onchange(
        "line_ids",
        "line_ids.amount_paid",
    )
    def _onchange_line_ids(self):

        # Le montant du paiement représente
        # le montant réellement reçu du membre.
        #
        # Il ne doit jamais être remplacé automatiquement
        # par le montant affecté aux cotisations.

        return

    # ==========================================================
    # CONTRAINTES MÉTIER
    # ==========================================================

    @api.constrains("member_id", "company_id")
    def _check_member_company(self):
        for record in self:
            if (
                record.member_id
                and record.company_id
                and record.member_id.company_id
                != record.company_id
            ):
                raise ValidationError(
                    _(
                        "Le membre et le paiement doivent appartenir "
                        "à la même filiale."
                    )
                )

    @api.constrains(
        "amount",
        "line_ids",
        "line_ids.amount_paid",
    )
    def _check_allocated_amount(self):
        for record in self:
            allocated_amount = sum(
                record.line_ids.mapped("amount_paid")
            )

            if allocated_amount > record.amount:
                raise ValidationError(
                    _(
                        "Le montant total affecté (%(allocated)s) "
                        "ne peut pas dépasser le montant du paiement "
                        "(%(amount)s)."
                    )
                    % {
                        "allocated": allocated_amount,
                        "amount": record.amount,
                    }
                )

    # ==========================================================
    # CRÉDITER ET VALIDER LE COMPTE MEMBRE
    # ==========================================================

    def _credit_member_account(
        self,
        amount,
        description=False,
    ):

        self.ensure_one()

        amount = amount or 0.0

        # ======================================================
        # CONTRÔLE DU MONTANT
        # ======================================================

        if amount <= 0:
            return False

        if not self.member_id:
            raise ValidationError(
                _(
                    "Aucun membre n'est associé "
                    "au paiement."
                )
            )

        # ======================================================
        # MODÈLES
        # ======================================================

        Account = self.env[
            "association.member.account"
        ]

        Transaction = self.env[
            "association.member.account.transaction"
        ]

        # ======================================================
        # RECHERCHE DU COMPTE MEMBRE
        # ======================================================

        account = Account.search(
            [
                (
                    "member_id",
                    "=",
                    self.member_id.id,
                ),
                (
                    "company_id",
                    "=",
                    self.company_id.id,
                ),
            ],
            limit=1,
        )

        # ======================================================
        # CRÉATION DU COMPTE SI NÉCESSAIRE
        # ======================================================

        if not account:

            account = Account.create(
                {
                    "member_id":
                        self.member_id.id,

                    "company_id":
                        self.company_id.id,
                }
            )

        # ======================================================
        # ÉVITER LE DOUBLE CRÉDIT
        # ======================================================

        existing_transaction = Transaction.search(
            [
                (
                    "account_id",
                    "=",
                    account.id,
                ),
                (
                    "payment_id",
                    "=",
                    self.id,
                ),
                (
                    "transaction_type",
                    "=",
                    "credit",
                ),
            ],
            limit=1,
        )

        if existing_transaction:

            return existing_transaction

        # ======================================================
        # CRÉATION DU MOUVEMENT DE CRÉDIT
        # ======================================================

        transaction = Transaction.create(
            {
                "account_id":
                    account.id,

                "transaction_type":
                    "credit",

                "amount":
                    amount,

                "transaction_date":
                    fields.Datetime.now(),

                "payment_id":
                    self.id,

                "description":
                    description
                    or _(
                        "Approvisionnement depuis "
                        "le paiement %(payment)s"
                    )
                    % {
                        "payment":
                            self.display_name,
                    },
            }
        )

        # ======================================================
        # VALIDATION RÉELLE DU MOUVEMENT
        #
        # ON UTILISE LE WORKFLOW DISPONIBLE
        # SUR LE MODÈLE DE TRANSACTION
        # ======================================================

        if hasattr(
            transaction,
            "action_validate",
        ):

            transaction.action_validate()

        elif hasattr(
            transaction,
            "action_post",
        ):

            transaction.action_post()

        elif hasattr(
            transaction,
            "action_confirm",
        ):

            transaction.action_confirm()

        # ======================================================
        # VÉRIFICATION DU MOUVEMENT
        # ======================================================

        transaction.invalidate_recordset()

        # ======================================================
        # ACTUALISATION DU COMPTE
        # ======================================================

        account.invalidate_recordset()

        if "balance" in account._fields:

            account.invalidate_recordset(
                [
                    "balance",
                ]
            )

            account.modified(
                [
                    "balance",
                ]
            )

        # ======================================================
        # ACTUALISATION DU MEMBRE
        # ======================================================

        self.member_id.invalidate_recordset()

        if "balance" in self.member_id._fields:

            self.member_id.invalidate_recordset(
                [
                    "balance",
                ]
            )

        return transaction
    
    # ==========================================================
    # ACTION - CHARGER LES COTISATIONS DISPONIBLES
    # ==========================================================

    def action_generate_subscription_lines(self):

        SubscriptionLine = self.env[
            "association.subscription.line"
        ]

        Period = self.env[
            "association.subscription.period"
        ]

        for record in self:

            if record.state != "draft":
                raise UserError(
                    _(
                        "Les cotisations peuvent uniquement "
                        "être chargées sur un paiement "
                        "en brouillon."
                    )
                )

            if not record.member_id:
                raise UserError(
                    _("Veuillez sélectionner un membre.")
                )

            # ======================================================
            # CYCLES RÉELLEMENT OUVERTS
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
                        record.company_id.id,
                    ),
                ]
            )

            running_subscription_ids = (
                running_periods.mapped(
                    "subscription_id"
                ).ids
            )

            if not running_subscription_ids:
                raise UserError(
                    _(
                        "Aucune cotisation ne possède "
                        "actuellement un cycle ouvert."
                    )
                )

            # ======================================================
            # COTISATIONS AUXQUELLES LE MEMBRE APPARTIENT
            # ======================================================

            subscription_lines = SubscriptionLine.search(
                [
                    (
                        "member_id",
                        "=",
                        record.member_id.id,
                    ),
                    (
                        "subscription_id",
                        "in",
                        running_subscription_ids,
                    ),
                    (
                        "subscription_id.company_id",
                        "=",
                        record.company_id.id,
                    ),
                ]
            )

            # ======================================================
            # CONSERVER UNIQUEMENT LES COTISATIONS NON SOLDÉES
            # POUR LE CYCLE OUVERT
            # ======================================================

            available_lines = (
                subscription_lines.filtered(
                    lambda line: (
                        line.balance or 0.0
                    ) > 0
                )
            )

            existing_subscription_line_ids = set(
                record.line_ids.mapped(
                    "subscription_line_id"
                ).ids
            )

            new_lines = []

            for subscription_line in available_lines:

                if (
                    subscription_line.id
                    in existing_subscription_line_ids
                ):
                    continue

                new_lines.append(
                    (
                        0,
                        0,
                        {
                            "subscription_line_id":
                                subscription_line.id,

                            "subscription_id":
                                subscription_line.subscription_id.id,

                            "amount_paid":
                                0.0,
                        },
                    )
                )

            if not new_lines:
                raise UserError(
                    _(
                        "Aucune cotisation disponible n'a été "
                        "trouvée pour le membre %(member)s.\n\n"
                        "Le membre doit appartenir à la cotisation "
                        "et la cotisation doit posséder un cycle ouvert."
                    )
                    % {
                        "member":
                            record.member_id.display_name,
                    }
                )

            record.write({
                "line_ids": new_lines,
            })

            record.message_post(
                body=_(
                    "%(count)s cotisation(s) avec cycle ouvert "
                    "chargée(s) pour %(member)s."
                )
                % {
                    "count":
                        len(new_lines),

                    "member":
                        record.member_id.display_name,
                }
            )

        return True

    # ==========================================================
    # ACTION - RÉPARTITION AUTOMATIQUE
    # ==========================================================

    def action_auto_allocate(self):
        for record in self:
            if record.state != "draft":
                raise UserError(
                    _(
                        "La répartition automatique est uniquement "
                        "possible sur un paiement en brouillon."
                    )
                )

            if record.amount <= 0:
                raise UserError(
                    _(
                        "Le montant du paiement doit être supérieur "
                        "à zéro."
                    )
                )

            if not record.line_ids:
                raise UserError(
                    _(
                        "Chargez d'abord les cotisations du membre."
                    )
                )

            remaining_amount = record.amount

            lines = record.line_ids.sorted(
                key=lambda line: (
                    (
                        line.subscription_id.current_period_id.due_date
                        if line.subscription_id.current_period_id
                        else fields.Date.today()
                    ),
                    line.id or 0,
                )
            )

            # ==========================================================
            # APPLIQUER LA PÉNALITÉ DU CYCLE
            # ==========================================================

            member_period = self.env[
                "association.subscription.period"
            ].search(
                [
                    (
                        "subscription_line_id",
                        "=",
                        subscription_line.id,
                    ),
                    (
                        "period_start_date",
                        "=",
                        period.period_start_date,
                    ),
                    (
                        "period_end_date",
                        "=",
                        period.period_end_date,
                    ),
                ],
                limit=1,
            )

            if member_period:

                member_period._apply_late_penalty()

                member_period.invalidate_recordset(
                    [
                        "penalty_amount",
                        "amount_paid",
                        "balance",
                        "payment_state",
                    ]
                )

            for line in lines:
                balance_to_pay = max(
                    line.balance_before_payment or 0.0,
                    0.0,
                )

                amount_to_allocate = min(
                    remaining_amount,
                    balance_to_pay,
                )

                line.amount_paid = amount_to_allocate

                remaining_amount -= amount_to_allocate

                if remaining_amount <= 0:
                    remaining_amount = 0.0

            record.message_post(
                body=_(
                    "Le montant du paiement a été réparti "
                    "automatiquement sur les cotisations."
                )
            )

        return True

    
    # ==========================================================
    # ACTION - ENCAISSER
    # ==========================================================

    def action_collect(self):

        for record in self:

            # ======================================================
            # CONTRÔLES
            # ======================================================

            if record.state != "draft":

                raise UserError(
                    _(
                        "Seul un paiement en brouillon "
                        "peut être encaissé."
                    )
                )

            if not record.member_id:

                raise ValidationError(
                    _("Veuillez sélectionner un membre.")
                )

            if record.amount <= 0:

                raise ValidationError(
                    _(
                        "Le montant reçu doit être "
                        "strictement supérieur à zéro."
                    )
                )

            # ======================================================
            # PASSAGE ENCAISSÉ
            #
            # IMPORTANT :
            # AUCUN IMPACT COTISATION
            # AUCUN IMPACT COMPTE MEMBRE
            # ======================================================

            record.write(
                {
                    "state": "collected",
                }
            )

            record.message_post(
                body=_(
                    "Encaissement enregistré.<br/>"
                    "Montant reçu : %(amount).2f %(currency)s.<br/>"
                    "Le paiement est en attente de validation."
                )
                % {
                    "amount":
                        record.amount,

                    "currency":
                        record.currency_id.name or "",
                }
            )

        return True    
    
    # ==========================================================
    # ACTION - VALIDER LE PAIEMENT
    # ==========================================================

    def action_confirm(self):

        for record in self:

            # ======================================================
            # CONTRÔLE ÉTAT
            # SEUL UN PAIEMENT ENCAISSÉ PEUT ÊTRE VALIDÉ
            # ======================================================

            if record.state != "collected":

                raise UserError(
                    _(
                        "Seul un paiement encaissé "
                        "peut être validé."
                    )
                )

            # ======================================================
            # CONTRÔLE MONTANT
            # ======================================================

            if record.amount <= 0:

                raise ValidationError(
                    _(
                        "Le montant du paiement doit être "
                        "strictement supérieur à zéro."
                    )
                )

            # ======================================================
            # LIGNES DE COTISATION CHOISIES
            # ======================================================

            subscription_lines = (
                record.line_ids
                .mapped("subscription_line_id")
                .filtered(lambda line: line)
            )

            # ======================================================
            # MONTANT AFFECTÉ
            # ======================================================

            allocated_amount = sum(
                record.line_ids.mapped(
                    "amount_paid"
                )
            )

            # ======================================================
            # CONTRÔLE DU MONTANT AFFECTÉ
            # ======================================================

            if allocated_amount < 0:

                raise ValidationError(
                    _(
                        "Le montant affecté ne peut pas "
                        "être négatif."
                    )
                )

            if allocated_amount > record.amount:

                raise ValidationError(
                    _(
                        "Le montant affecté aux cotisations "
                        "ne peut pas dépasser le montant "
                        "du paiement."
                    )
                )

            # ======================================================
            # CONTRÔLE DES AFFECTATIONS
            # ======================================================

            if record.has_allocations:

                if not record.line_ids:

                    raise ValidationError(
                        _(
                            "Vous avez choisi d'affecter "
                            "le paiement à des cotisations, "
                            "mais aucune cotisation "
                            "n'a été sélectionnée."
                        )
                    )

                invalid_lines = (
                    record.line_ids.filtered(
                        lambda line: (
                            not line.subscription_line_id
                            or
                            (line.amount_paid or 0.0) <= 0
                        )
                    )
                )

                if invalid_lines:

                    raise ValidationError(
                        _(
                            "Chaque ligne d'affectation doit "
                            "contenir une cotisation et un "
                            "montant strictement supérieur "
                            "à zéro."
                        )
                    )

            # ======================================================
            # CONTRÔLE DES COTISATIONS
            # ======================================================

            for line in record.line_ids:

                subscription_line = (
                    line.subscription_line_id
                )

                if not subscription_line:
                    continue

                subscription = (
                    subscription_line.subscription_id
                )

                period = (
                    subscription.current_period_id
                )

                # ==================================================
                # CONTRÔLE DU CYCLE
                # ==================================================

                if not period:

                    raise ValidationError(
                        _(
                            "Aucun cycle courant n'est ouvert "
                            "pour la cotisation "
                            "%(subscription)s."
                        )
                        % {
                            "subscription":
                                subscription.display_name,
                        }
                    )

                if period.state != "running":

                    raise ValidationError(
                        _(
                            "Le cycle %(cycle)s de la "
                            "cotisation %(subscription)s "
                            "n'est pas en cours."
                        )
                        % {
                            "cycle":
                                period.display_name,

                            "subscription":
                                subscription.display_name,
                        }
                    )

                # ==================================================
                # PAIEMENTS DÉJÀ VALIDÉS DU CYCLE
                #
                # IMPORTANT :
                # Le paiement actuel est exclu.
                # ==================================================

                other_payment_lines = (
                    subscription_line
                    .payment_line_ids
                    .filtered(
                        lambda payment_line: (
                            payment_line.payment_id
                            and
                            payment_line.payment_id.state
                            == "confirmed"
                            and
                            payment_line.payment_id.id
                            != record.id
                            and
                            payment_line.payment_id.payment_date
                            and
                            payment_line.payment_id.payment_date
                            >= period.period_start_date
                            and
                            payment_line.payment_id.payment_date
                            <= period.period_end_date
                        )
                    )
                )

                # ==================================================
                # TOTAL DÉJÀ PAYÉ
                # ==================================================

                already_paid = sum(
                    other_payment_lines.mapped(
                        "amount_paid"
                    )
                )

                # ==================================================
                # MONTANT TOTAL DÛ
                #
                # amount_due contient maintenant :
                #
                # COTISATION
                # +
                # PÉNALITÉ
                # ==================================================

                total_due = (
                    subscription_line.amount_due
                    or 0.0
                )

                # ==================================================
                # RESTE RÉEL AVANT LE PAIEMENT ACTUEL
                # ==================================================

                remaining_amount = max(
                    total_due - already_paid,
                    0.0,
                )

                # ==================================================
                # COTISATION DÉJÀ RÉGLÉE
                # ==================================================

                if remaining_amount <= 0:

                    raise ValidationError(
                        _(
                            "La cotisation %(subscription)s "
                            "est déjà réglée pour le cycle "
                            "%(cycle)s."
                        )
                        % {
                            "subscription":
                                subscription.display_name,

                            "cycle":
                                period.display_name,
                        }
                    )

                # ==================================================
                # CONTRÔLE DU MONTANT AFFECTÉ
                # ==================================================

                if (
                    line.amount_paid or 0.0
                ) > remaining_amount:

                    raise ValidationError(
                        _(
                            "Le montant affecté à %(member)s "
                            "dépasse le reste à payer.\n\n"
                            "Cotisation : %(subscription)s\n"
                            "Montant dû : "
                            "%(total_due).2f %(currency)s\n"
                            "Déjà payé : "
                            "%(already_paid).2f %(currency)s\n"
                            "Reste à payer : "
                            "%(balance).2f %(currency)s"
                        )
                        % {
                            "member":
                                subscription_line
                                .member_id
                                .display_name,

                            "subscription":
                                subscription.display_name,

                            "total_due":
                                total_due,

                            "already_paid":
                                already_paid,

                            "balance":
                                remaining_amount,

                            "currency":
                                record.currency_id.name
                                or "",
                        }
                    )

            # ======================================================
            # CONTRÔLE ORIGINE DU PAIEMENT
            #
            # - externe
            # - compte membre
            # ======================================================

            record._check_payment_source_values()

            # ======================================================
            # CALCUL DU SURPLUS
            # ======================================================

            surplus_amount = max(
                (record.amount or 0.0)
                - allocated_amount,
                0.0,
            )

            # ======================================================
            # TRAITEMENT DU SURPLUS
            #
            # Si le paiement comporte des affectations
            # et qu'un reste existe, le wizard doit obligatoirement
            # déterminer sa destination.
            # ======================================================

            if (
                record.has_allocations
                and surplus_amount > 0
                and not record.surplus_processed
            ):

                return {
                    "type": "ir.actions.act_window",
                    "name": _("Traitement du surplus"),
                    "res_model":
                        "association.payment.surplus.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "context": {
                        "default_payment_id":
                            record.id,

                        "default_surplus_amount":
                            surplus_amount,
                    },
                }

            # ======================================================
            # CRÉATION DU MOUVEMENT DU COMPTE DE VERSEMENT
            #
            # Cette méthode doit gérer uniquement les versements
            # externes destinés à un compte financier.
            # ======================================================

            record._create_receipt_fund_transaction()

            # ======================================================
            # VALIDATION DU PAIEMENT
            #
            # À PARTIR D'ICI LE PAIEMENT DEVIENT COMPTABILISÉ
            # DANS LES COTISATIONS.
            # ======================================================

            record.write(
                {
                    "state": "confirmed",
                }
            )

            # ======================================================
            # PAIEMENT DEPUIS LE COMPTE MEMBRE
            #
            # Le membre paie ses cotisations uniquement depuis
            # son compte membre.
            # ======================================================

            if (
                record.payment_source
                == "member_account"
            ):

                record._debit_member_account()

            # ======================================================
            # VERSEMENT EXTERNE SANS AFFECTATION
            #
            # Aucun règlement de cotisation.
            # Le montant approvisionne directement le compte membre.
            # ======================================================

            if (
                record.payment_source == "external"
                and not record.has_allocations
            ):

                record._credit_member_account(
                    record.amount
                )

            # ======================================================
            # ACTUALISATION DES LIGNES DE COTISATION
            #
            # Le paiement est maintenant CONFIRMED.
            # Le compute peut donc le prendre en compte.
            # ======================================================

            if subscription_lines:

                subscription_lines.invalidate_recordset(
                    [
                        "amount_due",
                        "amount_paid",
                        "balance",
                        "payment_state",
                        "payment_date",
                    ]
                )

                subscription_lines.modified(
                    [
                        "amount_due",
                        "amount_paid",
                        "balance",
                        "payment_state",
                        "payment_date",
                    ]
                )

            if record.meeting_id:
                meeting_fields = [
                    "collection_count",
                    "collection_paid_count",
                    "collection_pending_count",
                    "collection_total",
                    "pot_collected_amount",
                    "pot_allocated_amount",
                    "pot_available_amount",
                    "pot_beneficiary_count",
                ]
                record.meeting_id.invalidate_recordset(meeting_fields)
                record.meeting_id.modified(meeting_fields)

            # ======================================================
            # IMPORTANT
            # NE PAS RECRÉDITER AUTOMATIQUEMENT LE SURPLUS
            #
            # Le surplus a déjà été traité par le wizard :
            #
            # - compte membre
            # - compte financier
            # - remboursement
            #
            # L'ancien bloc :
            #
            # if surplus_amount > 0:
            #     record._credit_member_account(surplus_amount)
            #
            # EST SUPPRIMÉ.
            #
            # Sinon le surplus serait crédité deux fois.
            # ======================================================

            # ======================================================
            # MESSAGE
            # ======================================================

            message = _(
                "Le paiement a été validé."
            )

            if record.has_allocations:

                message += _(
                    "<br/>Montant affecté aux cotisations : "
                    "%(amount).2f %(currency)s"
                ) % {
                    "amount":
                        allocated_amount,

                    "currency":
                        record.currency_id.name
                        or "",
                }

            if surplus_amount > 0:

                message += _(
                    "<br/>Surplus traité : "
                    "%(amount).2f %(currency)s"
                ) % {
                    "amount":
                        surplus_amount,

                    "currency":
                        record.currency_id.name
                        or "",
                }

            record.message_post(
                body=message
            )

        return True 
        
    
    
    # ==========================================================
    # ACTION - ANNULER
    # ==========================================================

    def action_cancel(self):
        for record in self:
            if record.state == "cancelled":
                continue

            record.write({
                "state": "cancelled",
            })

            record._invalidate_subscription_lines()

            record.message_post(
                body=_(
                    "Le paiement a été annulé."
                )
            )

        return True

    # ==========================================================
    # ACTION - REMETTRE EN BROUILLON
    # ==========================================================

    def action_reset_draft(self):
        for record in self:
            if record.state != "cancelled":
                raise UserError(
                    _(
                        "Seul un paiement annulé peut être "
                        "remis en brouillon."
                    )
                )

            record.write({
                "state": "draft",
            })

            record._invalidate_subscription_lines()

            record.message_post(
                body=_(
                    "Le paiement a été remis en brouillon."
                )
            )

        return True

    # ==========================================================
    # CONTRÔLE DU MONTANT
    # ==========================================================

    @api.constrains("amount")
    def _check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError(
                    _(
                        "Le montant du paiement ne peut pas "
                        "être négatif."
                    )
                )

    # ==========================================================
    # WRITE
    # ==========================================================

    def write(self, vals):
        protected_fields = {
            "member_id",
            "company_id",
            "payment_date",
            "amount",
            "payment_method",
            "payment_reference",
            "line_ids",
        }

        if protected_fields.intersection(vals):
            confirmed_records = self.filtered(
                lambda record: record.state == "confirmed"
            )

            if confirmed_records:
                raise UserError(
                    _(
                        "Un paiement confirmé ne peut plus "
                        "être modifié."
                    )
                )

        return super().write(vals)
    
    # ==========================================================
    # ACTION - VOIR LES AFFECTATIONS
    # ==========================================================

    def action_view_payment_lines(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Affectations du paiement"),
            "res_model": "association.payment.line",
            "view_mode": "list,form",
            "domain": [
                (
                    "payment_id",
                    "=",
                    self.id,
                ),
            ],
            "context": {
                "default_payment_id": self.id,
                "create": self.state == "draft",
            },
        }
