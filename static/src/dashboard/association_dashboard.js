/** @odoo-module **/

import {
    Component,
    onWillStart,
    useState,
} from "@odoo/owl";

import {
    registry,
} from "@web/core/registry";

import {
    useService,
} from "@web/core/utils/hooks";


export class AssociationDashboard extends Component {

    static template =
        "primetech_association.AssociationDashboard";

    setup() {

        this.orm = useService("orm");

        this.action = useService("action");

        this.state = useState({

            loading: true,

            data: {
                company: {},
                members: {},
                meetings: {},
                subscriptions: {},
                payments: {},
                treasury: {},
                penalties: {recent: []},
                recent_payments: [],
                next_meeting: false,
                upcoming_meetings: [],
                recent_members: [],
                currency: {},
            },

        });

        onWillStart(
            async () => {

                await this.loadDashboard();

            }
        );

    }


    // =========================================================
    // CHARGEMENT
    // =========================================================

    async loadDashboard() {

        this.state.loading = true;

        try {

            const data = await this.orm.call(
                "association.dashboard",
                "get_dashboard_data",
                [],
            );

            this.state.data = data;

        } finally {

            this.state.loading = false;

        }

    }


    // =========================================================
    // FORMAT MONTANT
    // =========================================================

    formatAmount(amount) {

        const value = Number(
            amount || 0
        );

        return new Intl.NumberFormat(
            "fr-FR",
            {
                maximumFractionDigits: 0,
            }
        ).format(value);

    }

    todayLabel() {
        return new Intl.DateTimeFormat("fr-FR", {
            day: "2-digit", month: "short", year: "numeric",
        }).format(new Date());
    }

    get memberPercent() {
        const total = Number(this.state.data.members.total || 0);
        return total ? Math.round((Number(this.state.data.members.active || 0) / total) * 100) : 0;
    }

    get kpis() {
        const data = this.state.data;
        return [
            {label: "Membres actifs", value: this.formatAmount(data.members.active), icon: "fa-users", color: "purple", note: "Effectif actuel"},
            {label: "Total membres", value: this.formatAmount(data.members.total), icon: "fa-user-plus", color: "green", note: "Base des adhérents"},
            {label: "Cotisations collectées", value: this.formatAmount(data.payments.total), currency: true, icon: "fa-handshake-o", color: "orange", note: "Paiements confirmés"},
            {label: "Trésorerie", value: this.formatAmount(data.treasury.balance), currency: true, icon: "fa-credit-card", color: "blue", note: "Solde disponible"},
            {label: "Événements", value: this.formatAmount(data.meetings.upcoming), icon: "fa-calendar", color: "purple", note: "À venir"},
            {label: "Pénalités à traiter", value: this.formatAmount(data.penalties.pending), icon: "fa-gavel", color: "red", note: "À régulariser", negative: true},
        ];
    }

    get chartBars() {
        return [
            {month: "Janv.", height: 55}, {month: "Févr.", height: 65},
            {month: "Mars", height: 61}, {month: "Avr.", height: 72},
            {month: "Mai", height: 78}, {month: "Juin", height: 68},
        ];
    }

    get sections() {
        return [
            {name: "Actifs", value: this.memberPercent},
            {name: "Présences", value: Math.min(100, Number(this.state.data.meetings.last_attendance || 0))},
            {name: "À jour", value: Math.max(0, 100 - Math.min(100, Number(this.state.data.subscriptions.pending || 0)))},
            {name: "Participation", value: 58},
            {name: "Autres", value: 32},
        ];
    }


    // =========================================================
    // NAVIGATION
    // =========================================================

    async openAction(xmlId) {

        await this.action.doAction(xmlId);

    }


    openMembers() {

        return this.openAction(
            "primetech_association.action_association_member"
        );

    }


    openMeetings() {

        return this.openAction(
            "primetech_association.action_meeting"
        );

    }


    openSubscriptions() {

        return this.openAction(
            "primetech_association.action_subscription"
        );

    }


    openPayments() {

        return this.openAction(
            "primetech_association.action_payment"
        );

    }


    openTreasury() {

        return this.openAction(
            "primetech_association.action_association_fund"
        );

    }


    openPenalties() {

        return this.openAction(
            "primetech_association.action_penalty"
        );

    }

    openPenalty(penaltyId) {
        if (!penaltyId) {
            return;
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Sanction disciplinaire",
            res_model: "association.penalty",
            res_id: penaltyId,
            views: [[false, "form"]],
            target: "current",
        });
    }


    openMeeting(meetingId) {

        if (!meetingId) {
            return;
        }

        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Réunion",
            res_model: "association.meeting",
            res_id: meetingId,
            views: [
                [
                    false,
                    "form",
                ],
            ],
            target: "current",
        });

    }

}


registry
    .category("actions")
    .add(
        "primetech_association.dashboard",
        AssociationDashboard
    );
