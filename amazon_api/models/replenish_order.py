# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class ReplenishOrder(models.Model):
    _name = "replenish.order"

    name = fields.Char(string=u'单号')

    note = fields.Text(string=u'备注')

    date_order = fields.Datetime(default=lambda self: datetime.datetime.now(), string=u'订单日期')

    have_own_product = fields.Boolean(compute='_judge_have_own_product', store=False)
    have_other_product = fields.Boolean(compute='_judge_have_own_product', store=False)

    purchase_count = fields.Integer(compute='_compute_order_count', store=False, string=u'采购单数量')
    invoice_count = fields.Integer(compute='_compute_order_count', store=False, string=u'发票数量')
    delivery_count = fields.Integer(compute='_compute_order_count', store=False, string=u'发货单数量')

    total_amount = fields.Monetary(compute='_compute_total_amount', store=True, string=u'合计')

    sale_order_id = fields.Many2one('sale.order', domain=lambda self: self._get_sale_order_domain(), string=u'销售订单')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env['res.currency'].get_cny_currency(),
                                  string=u'币种')

    purchase_orders = fields.One2many('purchase.order', 'replenish_order_id')
    order_line = fields.One2many('replenish.order.line', 'order_id')
    invoices = fields.One2many('invoice', 'replenish_order_id', string=u'发票')
    deliveries = fields.One2many('stock.picking', 'replenish_order_id')

    state = fields.Selection([
        ('draft', u'草稿'),
        ('purchase', u'已转采'),
        ('delivering', u'待发货'),
        ('delivered', u'已发货'),
        ('cancel', u'取消')], default='draft', string=u'状态')
    delivery_type = fields.Selection([
        ('platform_purchase', u''),
        ('own_delivery', u''),
        ('both', u''),
    ], compute='_compute_delivery_type', store=False, string=u'发货类型')

    @api.multi
    def _judge_have_own_product(self):
        for record in self:
            have_own_product = False
            have_other_product = False
            for line in record.order_line:
                if line.own_product:
                    have_own_product = True
                else:
                    have_other_product = True
            record.have_own_product = have_own_product
            record.have_other_product = have_other_product

    @api.multi
    def _compute_delivery_type(self):
        for record in self:
            if record.have_own_product and record.have_other_product:
                record.delivery_type = 'both'
            elif record.have_other_product:
                record.delivery_type = 'platform_purchase'
            elif record.have_own_product:
                record.delivery_type = 'own_delivery'
            else:
                record.delivery_type = ''

    @api.multi
    def _compute_order_count(self):
        for record in self:
            record.purchase_count = len(record.purchase_orders)
            record.invoice_count = len(record.invoices)
            record.delivery_count = len(record.deliveries)

    @api.multi
    def view_delivery_order(self):
        self.ensure_one()
        return {
            'name': u'发货单',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.stock_picking_tree').id, 'tree'),
                      (self.env.ref('amazon_api.b2b_stock_picking_form').id, 'form')],
            'domain': [('replenish_order_id', '=', self.id)],
            'target': 'current',
        }

    @api.multi
    def view_invoice(self):
        self.ensure_one()
        return {
            'name': u'经销商发票',
            'type': 'ir.actions.act_window',
            'res_model': 'invoice',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.invoice_tree').id, 'tree'),
                (self.env.ref('amazon_api.invoice_form').id, 'form')],
            'domain': [('replenish_order_id', '=', self.id)],
            'target': 'current',
        }

    @api.multi
    def view_purchase_order(self):
        self.ensure_one()
        return {
            'name': u'采购单',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [
                (self.env.ref('amazon_api.purchase_order_tree').id, 'tree'),
                (self.env.ref('amazon_api.b2b_purchase_order_form').id, 'form')],
            'domain': [('replenish_order_id', '=', self.id)],
            'context': {'hide_supplier_price': True},
            'target': 'current',
        }

    @api.multi
    def platform_purchase(self):
        '''平台采购'''
        self.ensure_one()
        self.state = 'purchase'
        purchase_obj = self.env['purchase.order']
        #创建经销商发票并确认
        distributor_invoice = {
            'type': 'distributor',
            'detail_type': 'distributor_platform_purchase',
            'replenish_order_id': self.id,
            'origin': self.name,
            'order_line': [],
        }
        for line in self.order_line:
            if line.own_product:
                continue
            distributor_invoice['order_line'].append((0, 0, {
                'product_id': line.product_id.id,
                'platform_price': line.platform_price,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom.id,
                'freight': line.freight,
            }))
        if distributor_invoice.get('order_line'):
            invoice = self.env['invoice'].create(distributor_invoice)
            invoice.invoice_confirm()
        #创建采购单
        purchase_info = {}
        for line in self.order_line:
            if line.own_product:
                continue
            platform_pro_merchant = line.sudo().product_id.product_tmpl_id.merchant_id
            supplier_id = platform_pro_merchant.partner_id.id
            if purchase_info.has_key(supplier_id):
                purchase_info[supplier_id]['order_line'].append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'price_unit': line.product_id.supplier_price,
                    'taxes_id': [(6, False, [])],
                    'product_qty': line.product_uom_qty,
                    'product_uom': line.product_uom.id,
                    'date_planned': datetime.datetime.now(),
                    'freight': line.freight,
                    'replenish_line_id': line.id,
                }))
            else:
                purchase_info[supplier_id] = {
                    'replenish_order_id': self.id,
                    'merchant_id': platform_pro_merchant.id,
                    'partner_id': supplier_id,
                    'state': 'draft',
                    'origin': self.name,
                    'currency_id': self.currency_id.id,
                    'date_order': datetime.datetime.now(),
                    'date_planned': datetime.datetime.now(),
                    'order_line': [(0, 0, {
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'price_unit': line.product_id.supplier_price,
                        'taxes_id': [(6, False, [])],
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'date_planned': datetime.datetime.now(),
                        'freight': line.freight,
                        'replenish_line_id': line.id,
                    })]
                }
        for (supplier_id, val) in purchase_info.items():
            purchase_order = purchase_obj.create(val)

    @api.model
    def _get_sale_order_domain(self):
        user = self.env.user
        if self.user_has_groups('b2b_platform.b2b_shop_operator'):
            return [('shop_id', 'in', user.shop_ids.ids)]
        elif self.user_has_groups('b2b_platform.b2b_seller'):
            return [('merchant_id', '=', self.env.user.id)]
        else:
            return [('id', '=', 0)]

    @api.model
    def create(self, val):
        if not val.has_key('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('replenish.order.number') or '/'
        result = super(ReplenishOrder, self).create(val)
        return result

    @api.depends('order_line.total_amount')
    def _compute_total_amount(self):
        for record in self:
            total_amount = 0.0
            for line in record.order_line:
                total_amount += line.total_amount
            record.total_amount = total_amount

class ReplenishOrderLine(models.Model):
    _name = "replenish.order.line"

    platform_price = fields.Monetary(related='product_id.platform_price', store=True, readonly=True, string=u'平台采购价格')
    total_amount = fields.Monetary(compute='_compute_total_amount', store=True, string=u'合计')

    product_uom_qty = fields.Float(string=u'数量')
    freight = fields.Float(compute='_compute_freight', store=True, readonly=True, string=u'运费')

    own_product = fields.Boolean(compute='_compute_own_product', store=False, readonly=True, string=u'自有产品')

    order_id = fields.Many2one('replenish.order', ondelete='cascade')
    product_id = fields.Many2one('product.product', domain=[('state', '=', 'platform_published')], string=u'产品')
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', store=True, readonly=True,
                                  string=u'计量单位')
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id', store=True, string=u'币种')

    @api.depends('platform_price', 'product_uom_qty')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.platform_price * record.product_uom_qty + record.freight

    @api.multi
    def _compute_own_product(self):
        merchant = self.env.user.merchant_id or self.env.user
        for record in self:
            if record.product_id.product_tmpl_id.merchant_id == merchant:
                record.own_product = True
            else:
                record.own_product = False

    @api.multi
    @api.depends('product_id', 'order_id.sale_order_id')
    def _compute_freight(self):
        for record in self:
            tmpl = record.product_id.product_tmpl_id
            country = record.order_id.sale_order_id.country_id
            freight_obj = tmpl.freight_lines.filtered(lambda r: r.country_id == country)
            if freight_obj:
                record.freight = freight_obj.freight
            else:
                record.freight = 0
