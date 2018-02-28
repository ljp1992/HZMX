# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class Invoice(models.Model):
    _name = 'invoice'
    _order = 'id desc'

    name = fields.Char(string=u'单号')

    note = fields.Text(string=u'备注')

    total = fields.Float(compute='_compute_total', store=True, string=u'金额')

    date = fields.Date(string=u'日期', required=True, default=lambda self: fields.Date.today())

    merchant_id = fields.Many2one('res.users', string=u'经销商', required=True, readonly=True,
                                  default=lambda self: self.env.user, domain=[('user_type', '=', 'merchant')])
    sale_order_id = fields.Many2one('sale.order', string=u'销售订单')
    purchase_order_id = fields.Many2one('purchase.order', string=u'采购单')

    order_line = fields.One2many('invoice.line', 'order_id')

    state = fields.Selection([
        ('draft', u'新建'),
        ('paid', u'已付款'),
        ('cancel', u'已取消')], string=u'状态', default='draft')
    type = fields.Selection([
        ('distributor', u'经销商'),
        ('supplier', u'供应商'),
    ], string=u'发票类型')

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('account.invoice.number') or '/'
        return super(Invoice, self).create(val)

    @api.depends('order_line.total')
    def _compute_total(self):
        for record in self:
            total = 0
            for line in record.order_line:
                total += line.total
            record.total = total

    @api.multi
    def invoice_confirm(self):
        for record in self:
            record.state = 'paid'
            if record.type == 'distributor':
                record.merchant_id.account_amount -= record.total
            elif record.type == 'supplier':
                record.merchant_id.account_amount += record.total

class InvoiceLine(models.Model):
    _name = 'invoice.line'
    _order = 'id desc'

    order_id = fields.Many2one('invoice')
    product_id = fields.Many2one('product.product', string=u'产品')
    product_uom = fields.Many2one('product.uom', string=u'计量单位')

    platform_price = fields.Float(string=u'价格')
    product_uom_qty = fields.Float(string=u'数量')
    freight = fields.Float(string=u'运费')
    total = fields.Float(compute='_compute_total', store=True, string=u'小计')

    @api.depends('platform_price', 'product_uom_qty')
    def _compute_total(self):
        for record in self:
            record.total = record.platform_price * record.product_uom_qty + record.freight



