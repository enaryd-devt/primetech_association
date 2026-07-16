# -*- coding: utf-8 -*-

from odoo import api, models


class AssociationDashboard(models.AbstractModel):
    _name = "association.dashboard"
    _description = "Tableau de bord Association"

    # ==========================================================
    # DONNÉES DU TABLEAU DE BORD
    # ==========================================================

    @api.model
    def get_dashboard_data(self):

        company = self.env.company

        Member = self.env["association.member"]
        Meeting = self.env["association.meeting"]
        Payment = self.env["association.payment"]
        Subscription = self.env["association.subscription"]
        Fund = self.env["association.fund"]
        Penalty = self.env["association.penalty"]

        # ======================================================
        # MEMBRES
        # ======================================================

        member_domain = [
            ("company_id", "=", company.id),
        ]

        active_member_domain = member_domain + [
            ("state", "=", "active"),
        ]

        member_count = Member.search_count(
            member_domain
        )

        active_member_count = Member.search_count(
            active_member_domain
        )

        # ======================================================
        # RÉUNIONS
        # ======================================================

        meeting_domain = [
            ("company_id", "=", company.id),
        ]

        upcoming_meeting_domain = meeting_domain + [
            (
                "state",
                "in",
                [
                    "draft",
                    "confirmed",
                ],
            ),
        ]

        upcoming_meeting_count = Meeting.search_count(
            upcoming_meeting_domain
        )

        next_meeting = Meeting.search(
            upcoming_meeting_domain,
            order="meeting_date asc, id asc",
            limit=1,
        )

        upcoming_meetings = Meeting.search(
            upcoming_meeting_domain,
            order="meeting_date asc, id asc",
            limit=4,
        )

        # ======================================================
        # DERNIÈRE RÉUNION / PRÉSENCES
        # ======================================================

        last_meeting = Meeting.search(
            meeting_domain,
            order="meeting_date desc, id desc",
            limit=1,
        )

        last_attendance_count = 0

        if last_meeting:

            attendance_lines = last_meeting.attendance_ids

            Attendance = self.env[
                "association.attendance"
            ]

            if "state" in Attendance._fields:

                present_states = {
                    "present",
                    "late",
                }

                last_attendance_count = len(
                    attendance_lines.filtered(
                        lambda line:
                        line.state in present_states
                    )
                )

        # ======================================================
        # COTISATIONS
        # ======================================================

        subscription_domain = [
            ("company_id", "=", company.id),
        ]

        subscription_count = Subscription.search_count(
            subscription_domain
        )

        pending_subscription_count = 0

        if (
            "association.subscription.line"
            in self.env
        ):

            SubscriptionLine = self.env[
                "association.subscription.line"
            ]

            pending_subscription_count = (
                SubscriptionLine.search_count(
                    [
                        (
                            "company_id",
                            "=",
                            company.id,
                        ),
                        (
                            "payment_state",
                            "!=",
                            "paid",
                        ),
                    ]
                )
            )

        # ======================================================
        # ENCAISSEMENTS
        # ======================================================

        payment_domain = [
            ("company_id", "=", company.id),
        ]

        payment_count = Payment.search_count(
            payment_domain
        )

        confirmed_payments = Payment.search(
            payment_domain + [
                (
                    "state",
                    "in",
                    [
                        "paid",
                        "confirmed",
                        "collected",
                    ],
                ),
            ]
        )

        payment_total = sum(
            confirmed_payments.mapped("amount")
        )

        # ======================================================
        # TRÉSORERIE
        # ======================================================

        fund_domain = [
            ("company_id", "=", company.id),
        ]

        funds = Fund.search(
            fund_domain
        )

        treasury_balance = 0.0

        # ------------------------------------------------------
        # DÉTECTION DU CHAMP DE SOLDE
        # ------------------------------------------------------

        if "balance" in Fund._fields:

            treasury_balance = sum(
                funds.mapped("balance")
            )

        elif "current_balance" in Fund._fields:

            treasury_balance = sum(
                funds.mapped("current_balance")
            )

        elif "amount" in Fund._fields:

            treasury_balance = sum(
                funds.mapped("amount")
            )

        else:

            # ==================================================
            # CALCUL DEPUIS LES MOUVEMENTS FINANCIERS
            # ==================================================

            if (
                "association.fund.transaction"
                in self.env
            ):

                FundTransaction = self.env[
                    "association.fund.transaction"
                ]

                transaction_domain = []

                if "company_id" in FundTransaction._fields:

                    transaction_domain.append(
                        (
                            "company_id",
                            "=",
                            company.id,
                        )
                    )

                transactions = FundTransaction.search(
                    transaction_domain
                )

                for transaction in transactions:

                    # ------------------------------------------
                    # IGNORER LES MOUVEMENTS NON VALIDÉS
                    # ------------------------------------------

                    if "state" in FundTransaction._fields:

                        if transaction.state in (
                            "draft",
                            "cancel",
                            "cancelled",
                        ):

                            continue

                    # ------------------------------------------
                    # MONTANT
                    # ------------------------------------------

                    amount = transaction.amount or 0.0

                    # ------------------------------------------
                    # TYPE DE MOUVEMENT
                    # ------------------------------------------

                    transaction_type = False

                    if "transaction_type" in FundTransaction._fields:

                        transaction_type = (
                            transaction.transaction_type
                        )

                    elif "type" in FundTransaction._fields:

                        transaction_type = (
                            transaction.type
                        )

                    # ------------------------------------------
                    # CALCUL
                    # ------------------------------------------

                    if transaction_type in (
                        "debit",
                        "expense",
                        "out",
                        "withdrawal",
                    ):

                        treasury_balance -= amount

                    else:

                        treasury_balance += amount

        # ======================================================
        # DISCIPLINE
        # ======================================================

        penalty_domain = [
            ("company_id", "=", company.id),
        ]

        penalty_count = Penalty.search_count(
            penalty_domain
        )

        pending_penalty_count = Penalty.search_count(
            penalty_domain + [
                (
                    "state",
                    "in",
                    [
                        "draft",
                        "pending",
                    ],
                ),
            ]
        )

        # ======================================================
        # DERNIERS ENCAISSEMENTS
        # ======================================================

        recent_payments = Payment.search(
            payment_domain,
            order="payment_date desc, id desc",
            limit=5,
        )

        recent_payment_values = []

        for payment in recent_payments:

            recent_payment_values.append(
                {
                    "id":
                        payment.id,

                    "name":
                        payment.name or "",

                    "member":
                        (
                            payment.member_id.display_name
                            if payment.member_id
                            else ""
                        ),

                    "amount":
                        payment.amount or 0.0,

                    "state":
                        payment.state or "",

                    "date":
                        (
                            payment.payment_date.strftime(
                                "%d/%m/%Y"
                            )
                            if payment.payment_date
                            else ""
                        ),
                }
            )

        recent_members = Member.search(
            member_domain,
            order="join_date desc, id desc",
            limit=5,
        )
        recent_member_values = [
            {
                "id": member.id,
                "name": member.display_name or "",
                "state": dict(Member._fields["state"]._description_selection(self.env)).get(
                    member.state, member.state or ""
                ),
                "date": member.join_date.strftime("%d/%m/%Y")
                if member.join_date
                else "",
            }
            for member in recent_members
        ]

        upcoming_meeting_values = [
            {
                "id": meeting.id,
                "title": meeting.title or meeting.name or "",
                "date": meeting.meeting_date.strftime("%d/%m/%Y")
                if meeting.meeting_date
                else "",
                "time": dict(Meeting._fields["start_time"]._description_selection(self.env)).get(
                    meeting.start_time, meeting.start_time or ""
                ),
            }
            for meeting in upcoming_meetings
        ]

        # ======================================================
        # PROCHAINE RÉUNION
        # ======================================================

        next_meeting_value = False

        if next_meeting:

            next_meeting_value = {
                "id":
                    next_meeting.id,

                "name":
                    next_meeting.name or "",

                "date":
                    (
                        next_meeting.meeting_date.strftime(
                            "%d/%m/%Y"
                        )
                        if next_meeting.meeting_date
                        else ""
                    ),

                "location":
                    (
                        next_meeting.location
                        if hasattr(
                            next_meeting,
                            "location",
                        )
                        else ""
                    ),

                "state":
                    next_meeting.state or "",
            }

        # ======================================================
        # RÉSULTAT
        # ======================================================

        return {
            "user_name": self.env.user.name,
            "company": {
                "id":
                    company.id,

                "name":
                    company.display_name,
            },

            "members": {
                "total":
                    member_count,

                "active":
                    active_member_count,
            },

            "meetings": {
                "upcoming":
                    upcoming_meeting_count,

                "last_attendance":
                    last_attendance_count,
            },

            "subscriptions": {
                "total":
                    subscription_count,

                "pending":
                    pending_subscription_count,
            },

            "payments": {
                "count":
                    payment_count,

                "total":
                    payment_total,
            },

            "treasury": {
                "balance":
                    treasury_balance,
            },

            "penalties": {
                "total":
                    penalty_count,

                "pending":
                    pending_penalty_count,
            },

            "recent_payments":
                recent_payment_values,

            "recent_members": recent_member_values,

            "upcoming_meetings": upcoming_meeting_values,

            "next_meeting":
                next_meeting_value,

            "currency": {
                "symbol":
                    company.currency_id.symbol or "",

                "position":
                    company.currency_id.position or "after",
            },
        }
