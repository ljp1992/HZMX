# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class Invoice(models.Model):
    _name = 'invoice'
    _order = 'id desc'

    name = fields.Char(string=u'单号')

    note = fields.Text(string=u'备注')
    origin = fields.Char(string=u'来源')

    fba_freight = fields.Float(string=u'FBA运费')
    total = fields.Float(compute='_compute_total', store=True, string=u'金额')

    date = fields.Datetime(string=u'日期', required=True, default=lambda self: datetime.datetime.now())

    merchant_id = fields.Many2one('res.users', string=u'商户', required=True, readonly=True,
                                  default=lambda self: self.env.user, domain=[('user_type', '=', 'merchant')])
    sale_order_id = fields.Many2one('sale.order', string=u'销售订单')
    purchase_order_id = fields.Many2one('purchase.order', string=u'采购单')
    picking_id = fields.Many2one('stock.picking')

    order_line = fields.One2many('invoice.line', 'order_id')
    # transaction_details = fields.One2many('transaction.detail', 'invoice_id')

    state = fields.Selection([
        ('draft', u'新建'),
        ('paid', u'已付款'),
        ('cancel', u'已取消')], default='draft', string=u'状态')
    type = fields.Selection([
        ('distributor', u'经销商'),
        ('supplier', u'供应商'),
    ], string=u'发票类型')

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('account.invoice.number') or '/'
        result = super(Invoice, self).create(val)
        result.create_transaction_detail()
        return result

    @api.depends('order_line.total')
    def _compute_total(self):
        for record in self:
            total = 0
            for line in record.order_line:
                total += line.total
            record.total = total + record.fba_freight

    @api.multi
    def create_transaction_detail(self):
        for record in self:
            val = {}
            if record.type == 'distributor':
                val = {
                    'origin': record.name,
                    'invoice_id': record.id,
                    'type': 'distributor_invoice',
                    'state': 'draft',
                    'amount': 0 - record.total,
                }
            elif record.type == 'supplier':
                val = {
                    'origin': record.name,
                    'invoice_id': record.id,
                    'type': 'supplier_invoice',
                    'state': 'draft',
                    'amount': record.total,
                }
            if val:
                self.env['transaction.detail'].create(val)

    @api.multi
    def invoice_confirm(self):
        for record in self:
            if record.state == 'paid':
                continue
            record.state = 'paid'
            record.transaction_details.action_confirm()

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
        if context.get('view_own_invoice'):
            merchant_id = self.env.user.merchant_id or self.env.user
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('merchant_id', '=', merchant_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                args += [('merchant_id', '=', merchant_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        return super(Invoice, self).search(args, offset, limit, order, count=count)

class InvoiceLine(models.Model):
    _name = 'invoice.line'
    _order = 'id desc'

    order_id = fields.Many2one('invoice')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_uom = fields.Many2one('product.uom', string=u'计量单位')
    operation_line_id = fields.Many2one('stock.pack.operation')

    platform_price = fields.Float(string=u'价格')
    product_uom_qty = fields.Float(string=u'数量')
    freight = fields.Float(string=u'运费')
    total = fields.Float(compute='_compute_total', store=True, string=u'小计')

    @api.depends('platform_price', 'product_uom_qty', 'freight')
    def _compute_total(self):
        for record in self:
            record.total = (record.platform_price + record.freight) * record.product_uom_qty



