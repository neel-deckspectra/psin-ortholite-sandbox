/** @odoo-module **/

import { VisitorForm } from "@frontdesk/visitor_form/visitor_form";
import { Frontdesk } from "@frontdesk/frontdesk";
import { patch } from "@web/core/utils/patch";
import { Component, onMounted, onWillUnmount, useRef, useState } from "@odoo/owl";
import { WelcomePage } from "@frontdesk/welcome_page/welcome_page";
import { RegisterPage } from "@frontdesk/register_page/register_page";
import { DrinkPage } from "@frontdesk/drink_page/drink_page";
import { HostPage } from "@frontdesk/host_page/host_page";
import { EndPage } from "@frontdesk/end_page/end_page";

patch(Frontdesk.prototype, {

    get frontdeskProps() {
        let props = {};
        if (this.state.currentComponent === WelcomePage) {
            props = {
                showScreen: this.showScreen.bind(this),
                resetData: this.resetData.bind(this),
                onChangeLang: this.onChangeLang.bind(this),
                token: this.token,
                companyName: this.frontdeskData.company.name,
                stationInfo: this.station,
                langs: this.frontdeskData.langs.length > 1 ? this.frontdeskData.langs : false,
                currentLang: this.props.currentLang,
            };
        } else if (this.state.currentComponent === VisitorForm) {
            props = {
                onChangeLang: this.onChangeLang.bind(this),
                showScreen: this.showScreen.bind(this),
                clearUpdatePlannedVisitors: this.clearUpdatePlannedVisitors.bind(this),
                setVisitorData: this.setVisitorData.bind(this),
                updatePlannedVisitors: this.updatePlannedVisitors.bind(this),
                visitorData: this.visitorData || false,
                isMobile: this.props.isMobile,
                currentComponent: this.state.currentComponent.name,
                isPlannedVisitors: this.state.plannedVisitors.length ? true : false,
                stationInfo: this.station,
                langs: this.frontdeskData.langs.length > 1 ? this.frontdeskData.langs : false,
                currentLang: this.props.currentLang,
                theme: this.station.theme,
            };
        } else if (this.state.currentComponent === HostPage) {
            props = {
                stationId: this.station.id,
                token: this.token,
                showScreen: this.showScreen.bind(this),
                setHostData: this.setHostData.bind(this),
            };
        } else if (this.state.currentComponent === RegisterPage) {
            props = {
                showScreen: this.showScreen.bind(this),
                onClose: this.onClose.bind(this),
                checkOut: this.checkOut.bind(this),
                createVisitor: this.createVisitor.bind(this),
                theme: this.station.theme,
                isMobile: this.props.isMobile,
                isDrinkVisible: this.frontdeskData.drinks?.length ? true : false,
                plannedVisitorData: this.plannedVisitorData,
                hostData: this.hostData,
            };
        } else if (this.state.currentComponent === DrinkPage) {
            props = {
                showScreen: this.showScreen.bind(this),
                setDrink: this.setDrink.bind(this),
                theme: this.station.theme,
                drinkInfo: this.frontdeskData.drinks,
                stationId: this.props.id,
                token: this.token,
                visitorId: this.plannedVisitorData
                    ? this.plannedVisitorData.plannedVisitorId
                    : this.visitorId,
            };
        } else if (this.state.currentComponent === EndPage) {
            props = {
                showScreen: this.showScreen.bind(this),
                onClose: this.onClose.bind(this),
                isMobile: this.props.isMobile,
                isDrinkSelected: this.isDrinkSelected,
                theme: this.station.theme,
                plannedVisitorData: this.plannedVisitorData,
                hostData: this.hostData,
            };
        }
        return props;
    },

	/* This method creates the visitor in the backend through rpc call */
    async createVisitor() {
        const result = await this.rpc(`${this.frontdeskUrl}/prepare_visitor_data`, {
            name: this.visitorData.visitorName,
            phone: this.visitorData.visitorPhone,
            email: this.visitorData.visitorEmail,
            company: this.visitorData.visitorCompany,
            reason_for_visiting: this.visitorData.visitReason,
            govt_id: this.visitorData.govtID,
            oin_id_visitor_number: this.visitorData.oinIDvisitor_number,
            electronic_device: this.visitorData.electronicDevice,
            host_ids: this.hostData ? [this.hostData.hostId] : []
        });
        this.visitorId = result.visitor_id;
        // this.rpc(`${this.frontdeskUrl}/send_whatsapp_alert`, {
        //     visitor_id : this.visitorId
        // });
    },

	/**
     * @param {string} name
     * @param {string|false} phone
     * @param {string|false} email
     * @param {string|false} company
     */
    setVisitorData(name, phone, email, company, reason_for_visiting, govt_id, oin_id_visitor_number, electronic_device) {
        this.visitorData = {
            visitorName: name,
            visitorPhone: phone,
            visitorEmail: email,
            visitorCompany: company,
            visitReason: reason_for_visiting,
            govtID: govt_id,
            oinIDvisitor_number: oin_id_visitor_number,
            electronicDevice: electronic_device,
        };
    },
    async checkOut() {
        const result = await this.rpc(`${this.frontdeskUrl}/visitor_checkout`, {
        	visitor_id : this.visitorId
        });
        !this.props.isMobile ? this.showScreen("WelcomePage") : this.showScreen("VisitorForm");
    },
});

patch(VisitorForm.prototype, {
    setup() {
    	super.setup();
    	this.inputVisitReasonRef = useRef("visitReason");
        this.inputGovtIdRef = useRef("govtID");
        this.inputoinIDvisitor_numberRef = useRef("oinIDvisitor_number");
        this.inputElectronicDeviceRef = useRef("electronicDevice");
    },

	/**
     * @private
     */
    _onSubmit() {
        this.props.setVisitorData(
            this.inputNameRef.el.value,
            this.inputPhoneRef.el?.value || false,
            this.inputEmailRef.el?.value || false,
            this.inputCompanyRef.el?.value || false,
            this.inputVisitReasonRef.el?.value || false,
            this.inputGovtIdRef.el?.value || false,
            this.inputoinIDvisitor_numberRef.el?.value || false,
            this.inputElectronicDeviceRef.el?.value || false,
        );
        // Show the HostPage component, if the host_selection field is true from the backend
        this.props.stationInfo.host_selection
            ? this.props.showScreen("HostPage")
            : this.props.showScreen("RegisterPage");
    },
});
