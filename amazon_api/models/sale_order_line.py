# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    order_item_id = fields.Char(string=u'Order Item Id')

    own_product = fields.Boolean(compute='_own_product', store=False, string=u'自有产品')

    usable_inventory = fields.Float(compute='_compute_usable_inventory', store=False, readonly=True, string=u'可用库存')
    # usable_inventory = fields.Float(related='product_id.usable_invnetory', store=False, readonly=True, string=u'可用库存')
    e_price_unit = fields.Float(string=u'单价')
    price_unit = fields.Monetary(related='product_id.platform_price', store=True, string=u'单价')
    e_freight = fields.Float(string=u'运费')
    supplier_freight = fields.Float(compute='_supplier_freight', string=u'运费')
    b2b_subtotal = fields.Float(compute='_compute_b2b_subtotal', store=False, string=u'小计')

    shop_product_id = fields.Many2one('product.product', domain=[('state', '=', 'shop')], string=u'商品')
    e_currency_id = fields.Many2one('amazon.currency', related='order_id.e_currency_id', string=u'币种')

    b2b_state = fields.Selection([
        ('wait_handle', u'待处理'),
        ('delivering', u'待发货'),
        ('delivered', u'已交付'),
        ('cancel', u'取消')], related='order_id.b2b_state', string=u'状态')

    @api.depends('product_id')
    def _compute_usable_inventory(self):
        for record in self:
            record.usable_inventory = self.env['product.product'].get_product_usable_inventory(record.product_id)

    api.multi
    def _compute_b2b_subtotal(self):
        for record in self:
            record.b2b_subtotal = (record.price_unit + record.supplier_freight) * record.product_uom_qty

    @api.multi
    def _own_product(self):
        for line in self:
            merchant = line.sudo().order_id.shop_id.seller_id.merchant_id
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

