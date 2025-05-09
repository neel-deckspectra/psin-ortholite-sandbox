from odoo import http, fields
from odoo.http import request
from odoo.addons.frontdesk.controllers.main import Frontdesk


class FrontdeskExtend(Frontdesk):
    @http.route(
        "/frontdesk/<int:frontdesk_id>/<string:token>/prepare_visitor_data",
        type="json",
        auth="public",
        methods=["POST"],
    )
    def prepare_visitor_data(self, frontdesk_id, token, visitor_id=None, **kwargs):
        result = super().prepare_visitor_data(frontdesk_id, token, visitor_id, **kwargs)
        if isinstance(result, dict):
            visitor = request.env["frontdesk.visitor"].browse(result["visitor_id"])
            visitor.sudo().write(
                {
                    "visiting_reason": kwargs.get("reason_for_visiting"),
                    "govt_id": kwargs.get("govt_id"),
                    "oin_id_visitor_number": kwargs.get("oin_id_visitor_number"),
                    "electronic_device": kwargs.get("electronic_device"),
                }
            )
        else:
            visitor = request.env["frontdesk.visitor"].browse(visitor_id)
            visitor.sudo().write(
                {
                    "visiting_reason": kwargs.get("reason_for_visiting"),
                    "govt_id": kwargs.get("govt_id"),
                    "oin_id_visitor_number": kwargs.get("oin_id_visitor_number"),
                    "electronic_device": kwargs.get("electronic_device"),
                }
            )
        return result

    @http.route(
        "/frontdesk/<int:frontdesk_id>/<string:token>/visitor_checkout",
        type="json",
        auth="public",
        methods=["POST"],
    )
    def visitor_check_out(self, frontdesk_id, token, visitor_id=None, **kwargs):
        visitor = request.env["frontdesk.visitor"].browse(visitor_id)
        visitor.sudo().write({"state": "checked_out"})

    @http.route(
        "/frontdesk/<int:frontdesk_id>/<string:token>/send_whatsapp_alert",
        type="json",
        auth="public",
        methods=["POST"],
    )
    def visitor_whatsapp_alert(self, frontdesk_id, token, visitor_id=None, **kwargs):
        visitor = request.env["frontdesk.visitor"].browse(visitor_id)
        wa_template_id = (
            request.env["whatsapp.template"]
            .sudo()
            .search(
                [
                    ("model", "=", "frontdesk.visitor"),
                    ("status", "=", "approved"),
                    "|",
                    ("allowed_user_ids", "=", False),
                    ("allowed_user_ids", "in", request.env.user.ids),
                ]
            )
        )
        visit_tmpl_id = wa_template_id.filtered(
            lambda l: l.template_name == "visiting_notification"
        )
        if visit_tmpl_id:
            vals = {
                "res_ids": [visitor.id],
                "res_model": "frontdesk.visitor",
                "phone": visitor.phone,
                "wa_template_id": visit_tmpl_id.id,
            }
            composer = request.env["whatsapp.composer"].sudo().create(vals)
            composer.with_context(
                wa_template_id=visit_tmpl_id.id, phone=visitor.phone
            ).action_send_whatsapp_template()
