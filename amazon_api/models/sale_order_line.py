# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_item_id = fields.Char(string=u'Order Item Id')

    own_product = fields.Boolean(compute='_own_product', store=False, string=u'自有产品')

    e_price_unit = fields.Float(string=u'单价')
    e_freight = fields.Float(string=u'运费')

    shop_product_id = fields.Many2one('product.product', string=u'商品')
    e_currency_id = fields.Many2one('amazon.currency', related='order_id.e_currency_id', string=u'币种')

    @api.multi
    def _own_product(self):
        for line in self:
            if line.product_id.product_tmpl_id.merchant_id == self.env.user:
                line.own_product = True
            else:
                line.own_product = False


