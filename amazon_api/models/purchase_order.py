# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    own_data = fields.Boolean(search='_own_data_search', store=False)

    sale_order_id = fields.Many2one('sale.order')

    delivery_order_count = fields.Integer(compute='_delivery_order_count')

    deliverys = fields.One2many('stock.picking', 'purchase_order_id')

    platform_purchase_state = fields.Selection([
        ('draft', u'草稿'),
        ('send', u'已发送'),
        ('done', u'完成'),
    ], default='draft', string=u'平台采购状态')

    @api.model
    def _own_data_search(self, operator, value):
        print '_own_data_search purchase'
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
                (self.env.ref('stock.vpicktree').id, 'tree'),
                (self.env.ref('stock.view_picking_form').id, 'form')],
            'domain': [('id', 'in', self.deliverys.ids)],
            'target': 'current',
        }

    @api.multi
    def confirm_purchase_ljp(self):
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
        stock_picking_obj.create(delivery_info)
        return

    @api.multi
    def _delivery_order_count(self):
        for purchase in self:
            purchase.delivery_order_count = len(purchase.deliverys)