# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class Invoice(models.Model):
    _name = 'invoice'
    _order = 'id desc'

    name = fields.Char(string=u'单号')

    note = fields.Text(string=u'备注')
    origin = fields.Char(string=u'相关单号')

    fba_freight = fields.Float(string=u'FBA运费')
    total = fields.Float(compute='_compute_total', store=True, string=u'金额')

    paid_time = fields.Datetime(string=u'结算时间')

    merchant_id = fields.Many2one('res.users', string=u'商户', required=True, readonly=True,
                                  default=lambda self: self.env.user, domain=[('user_type', '=', 'merchant')])
    sale_order_id = fields.Many2one('sale.order', string=u'销售订单')
    purchase_order_id = fields.Many2one('purchase.order', string=u'采购单')
    picking_id = fields.Many2one('stock.picking')

    order_line = fields.One2many('invoice.line', 'order_id')

    state = fields.Selection([
        ('draft', u'未结算'),
        ('done', u'已结算'),
        ('cancel', u'已取消')], default='draft', string=u'状态')
    type = fields.Selection([
        ('distributor_platform_purchase', u'平台采购'),
        ('distributor_own_delivery', u'自有产品第三方仓库发货'),
        ('distributor_fba', u'FBA补货'),
        ('supplier_own_stock', u'自有仓库发货'),
        ('supplier_third_stock', u'第三方仓库发货'),
        ('supplier_fba_own_stock', u'FBA自有仓库发货'),
        ('supplier_fba_third_stock', u'FBA第三方仓库发货'),
    ], string=u'发票类型')


    @api.depends('order_line.total')
    def _compute_total(self):
        for record in self:
            total = 0
            for line in record.order_line:
                total += line.total
            record.total = total + record.fba_freight

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



