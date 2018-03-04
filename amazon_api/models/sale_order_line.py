# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_item_id = fields.Char(string=u'Order Item Id')

    own_product = fields.Boolean(compute='_own_product', store=False, string=u'自有产品')

    e_price_unit = fields.Float(string=u'单价')
    e_freight = fields.Float(string=u'运费')
    supplier_freight = fields.Float(compute='_supplier_freight', string=u'运费')
    b2b_subtotal = fields.Float(compute='_compute_b2b_subtotal', store=False, string=u'小计')

    shop_product_id = fields.Many2one('product.product', string=u'商品')
    e_currency_id = fields.Many2one('amazon.currency', related='order_id.e_currency_id', string=u'币种')

    b2b_state = fields.Selection([
        ('wait_handle', u'待处理'),
        ('delivering', u'待发货'),
        ('delivered', u'已交付'),
        ('cancel', u'取消')], related='order_id.b2b_state', string=u'状态')

    api.multi
    def _compute_b2b_subtotal(self):
        for record in self:
            print 111
            record.b2b_subtotal = (record.price_unit + record.supplier_freight) * record.product_uom_qty

    @api.multi
    def _own_product(self):
        for line in self:
            merchant = self.env.user.merchant_id or self.env.user
            if line.product_id.product_tmpl_id.merchant_id == merchant:
                line.own_product = True
            else:
                line.own_product = False

    @api.multi
    def _supplier_freight(self):
        for record in self:
            tmpl = record.product_id.product_tmpl_id
            country = record.order_id.country_id
            freight_obj = tmpl.freight_lines.filtered(lambda r: r.country_id == country)
            if freight_obj:
                record.supplier_freight = freight_obj.freight
            else:
                record.supplier_freight = 0

