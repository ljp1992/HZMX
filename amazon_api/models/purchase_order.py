# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    freight = fields.Float(compute='_compute_freight', store=False, string=u'运费')

    b2b_delivery_count = fields.Integer(compute='_b2b_delivery_count')
    b2b_invoice_count = fields.Integer(compute='_b2b_invoice_count')
    b2b_total = fields.Float(compute='_compute_total', store=False, string=u'合计')

    own_data = fields.Boolean(search='_own_data_search', store=False)
    hide_delivery_button = fields.Boolean(compute='_hide_delivery_button')

    sale_order_id = fields.Many2one('sale.order')

    delivery_order_count = fields.Integer(compute='_delivery_order_count')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')
    e_country_id = fields.Many2one('amazon.country', related='sale_order_id.country_id', string=u'发往国家')

    deliverys = fields.One2many('stock.picking', 'purchase_order_id')
    b2b_invoice_ids = fields.One2many('invoice', 'purchase_order_id', string=u'发票')

    platform_purchase_state = fields.Selection([
        ('draft', u'待处理'),
        ('send', u'待发货'),
        ('done', u'已发货'),
    ], default='draft', string=u'状态')

    def _hide_delivery_button(self):
        merchant = self.env.user.merchant_id or self.env.user
        for record in self:
            if record.merchant_id == merchant:
                record.hide_delivery_button = False
            else:
                record.hide_delivery_button = True
            if record.platform_purchase_state != 'send':
                record.hide_delivery_button = True

    def _compute_total(self):
        for record in self:
            total = 0
            for line in record.order_line:
                total += line.b2b_total
            record.b2b_total = total

    def _compute_freight(self):
        for record in self:
            freight = 0
            for line in record.order_line:
                freight += line.freight
            record.freight = freight

    def _b2b_delivery_count(self):
        for record in self:
            record.b2b_delivery_count = len(record.deliverys)

    def _b2b_invoice_count(self):
        for record in self:
            record.b2b_invoice_count = len(record.b2b_invoice_ids)

    def view_invoice(self):
        return {
            'name': u'供应商发票',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('b2b_platform.invoice_tree').id, 'tree'),
                (self.env.ref('b2b_platform.supplier_invoice_form').id, 'form')],
            'domain': [('id', 'in', self.b2b_invoice_ids.ids)],
            'target': 'current',
        }

    @api.model
    def _own_data_search(self, operator, value):
        user = self.env.user
        if user.user_type == 'operator':
            return [('id', '=', 0)]
        elif user.user_type == 'merchant':
            return [('partner_id', '=', user.partner_id.id)]
        else:
            return []

    @api.multi
    def view_delivery_order(self):
        return {
            'name': u'发货单',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.stock_picking_tree').id, 'tree'),
                (self.env.ref('amazon_api.stock_picking_form').id, 'form')],
            'domain': [('id', 'in', self.deliverys.ids)],
            'target': 'current',
        }

    @api.multi
    def confirm_purchase_ljp(self):
        '''发货'''
        self.ensure_one()
        self.platform_purchase_state = 'send'
        loc_obj = self.env['stock.location']
        stock_picking_obj = self.env['stock.picking']
        sale_order = self.sale_order_id
        location_id = loc_obj.search([
            ('partner_id', '=', self.partner_id.id),
            ('location_id', '=', self.env.ref('b2b_platform.supplier_stock').id)], limit=1).id
        location_dest_id = self.env.ref('stock.stock_location_customers').id
        delivery_info = {
            'partner_id': self.partner_id.id,
            'merchant_id': self.env.user.merchant_id.id or self.env.user.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'picking_type_id': 3,
            'purchase_order_id': self.id,
            'sale_order_id': sale_order.id,
            'country_id': sale_order.country_id.id,
            'province': sale_order.state,
            'city': sale_order.city,
            'phone': sale_order.phone,
            'street': sale_order.street,
            'postal_code': sale_order.postal_code,
            'e_mail': sale_order.e_mail,
            'move_lines': [],
        }
        for pur_line in self.order_line:
            delivery_info['move_lines'].append((0, 0, {
                'product_id': pur_line.product_id.id,
                'name': pur_line.product_id.name,
                'product_uom_qty': pur_line.product_qty,
                'product_uom': pur_line.product_uom.id,
            }))
        delivery = stock_picking_obj.create(delivery_info)
        delivery.action_confirm()
        delivery.action_assign()
        return

    @api.multi
    def _delivery_order_count(self):
        for purchase in self:
            purchase.delivery_order_count = len(purchase.deliverys)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    freight = fields.Float(compute='_compute_freight', store=False, string=u'运费')
    b2b_total = fields.Float(compute='_compute_total', store=False, string=u'小计')

    def _compute_total(self):
        for record in self:
            record.b2b_total = record.price_unit * record.product_qty + record.freight

    @api.multi
    def _compute_freight(self):
        for record in self:
            tmpl = record.product_id.product_tmpl_id
            country = record.order_id.e_country_id
            freight_obj = tmpl.freight_lines.filtered(lambda r: r.country_id == country)
            if freight_obj:
                record.freight = freight_obj.freight
            else:
                record.freight = 0

