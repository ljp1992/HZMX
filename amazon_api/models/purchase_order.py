# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    origin = fields.Char(string=u'来源单据')

    freight = fields.Float(compute='_compute_freight', store=False, string=u'运费')

    b2b_delivery_count = fields.Integer(compute='_b2b_delivery_count')
    b2b_invoice_count = fields.Integer(compute='_b2b_invoice_count')

    b2b_total = fields.Float(compute='_compute_total', store=False, string=u'合计')
    fba_freight = fields.Float(string=u'FBA运费')

    own_data = fields.Boolean(search='_own_data_search', store=False)
    own_record = fields.Boolean(compute='_own_record')
    hide_delivery_button = fields.Boolean(compute='_hide_delivery_button')

    delivery_order_count = fields.Integer(compute='_delivery_order_count')

    sale_order_id = fields.Many2one('sale.order')
    fba_replenish_id = fields.Many2one('fba.replenish', string=u'FBA补货单')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')
    e_country_id = fields.Many2one('amazon.country', related='sale_order_id.country_id', string=u'发往国家')

    deliverys = fields.One2many('stock.picking', 'purchase_order_id')
    b2b_invoice_ids = fields.One2many('invoice', 'purchase_order_id', string=u'发票')

    b2b_state = fields.Selection([
        ('draft', u'待发货'),
        ('confirmed', u'已确认'),
        ('done', u'已发货'),
    ], default='draft', string=u'状态')
    origin_type = fields.Selection([
        ('FBA', u'FBA补货'),
        ('sale', u'客户订单'),
    ], default='sale', string=u'来源')

    @api.multi
    def _own_record(self):
        merchant = self.env.user.merchant_id or self.env.user
        for record in self:
            if record.partner_id == merchant.partner_id:
                record.own_record = True
            else:
                record.own_record = False

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
            record.b2b_total = total + record.fba_freight

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
                (self.env.ref('amazon_api.invoice_tree').id, 'tree'),
                (self.env.ref('amazon_api.invoice_form').id, 'form')],
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
                (self.env.ref('amazon_api.b2b_stock_picking_form').id, 'form')],
            'domain': [('id', 'in', self.deliverys.ids)],
            'target': 'current',
        }

    @api.multi
    def confirm_purchase_ljp(self):
        '''确认采购单'''
        self.ensure_one()
        self.b2b_state = 'confirmed'
        stock_picking_obj = self.env['stock.picking']
        loc_obj = self.env['stock.location']
        merchant = self.env.user.merchant_id or self.env.user
        location = loc_obj.search([
            ('partner_id', '=', merchant.partner_id.id),
            ('location_id', '=', self.env.ref('b2b_platform.third_warehouse').id)], limit=1)
        if not location:
            location = loc_obj.search([
                ('partner_id', '=', merchant.partner_id.id),
                ('location_id', '=', self.env.ref('b2b_platform.supplier_stock').id)], limit=1)
        if not location:
            raise UserError(u'Not found supplier b2b location!')
        location_dest_id = self.env.ref('stock.stock_location_customers').id
        origin_type = ''
        if self.origin_type == 'FBA':
            origin_type = 'fba_delivery'
        elif self.origin_type == 'sale':
            origin_type = 'agent_delivery'
        val = {
            'partner_id': merchant.partner_id.id,
            'merchant_id': merchant.id,
            'location_id': location.id,
            'location_dest_id': location_dest_id,
            'picking_type_id': 4,
            'b2b_type': 'outgoing',
            'origin_type': origin_type,
            'origin': self.name,
            'purchase_order_id': self.id or False,
            'sale_order_id': self.sale_order_id.id or False,
            'fba_replenish_id': self.fba_replenish_id.id or False,
            'pack_operation_product_ids': [],
        }
        for line in self.order_line:
            val['pack_operation_product_ids'].append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_qty,
                'qty_done': line.product_qty,
                'product_uom_id': line.product_uom.id,
                'location_id': location.id,
                'location_dest_id': location_dest_id,
                'b2b_purchase_line_id': line.id,
                'b2b_sale_line_id': line.b2b_sale_line_id.id or False,
                'fba_replenish_line_id': line.fba_replenish_line_id.id or False,
            }))
        delivery = stock_picking_obj.create(val)
        delivery.create_delivery_info()
        return {
            'name': u'代理发货',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.stock_picking_tree').id, 'tree'),
                      (self.env.ref('amazon_api.b2b_stock_picking_form').id, 'form')],
            'domain': [('id', '=', delivery.id)],
            'target': 'current',
        }

    @api.multi
    def _delivery_order_count(self):
        for purchase in self:
            purchase.delivery_order_count = len(purchase.deliverys)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += [('name', operator, name)]
        result = self.search(args, limit=limit)
        return result.name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self.env.context or {}
        if context.get('view_own_purchase'):
            merchant_id = self.env.user.merchant_id or self.env.user
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('partner_id', '=', merchant_id.partner_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                args += [('partner_id', '=', merchant_id.partner_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        return super(PurchaseOrder, self).search(args, offset, limit, order, count=count)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    freight = fields.Float(store=True, string=u'运费')
    b2b_total = fields.Float(compute='_compute_total', store=False, string=u'小计')

    b2b_sale_line_id = fields.Many2one('sale.order.line')
    fba_replenish_line_id = fields.Many2one('fba.replenish.line')

    def _compute_total(self):
        for record in self:
            record.b2b_total = record.price_unit * record.product_qty + record.freight


