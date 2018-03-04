# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError

class FbaReplenish(models.Model):
    _name = 'fba.replenish'
    _order = 'id desc'

    name = fields.Char(string=u'单号')

    note = fields.Text(u'备注')

    freight = fields.Float(string=u'运费(元)', digits=(16,2))

    country_id = fields.Many2one('amazon.country', string=u'发往国家', required=True)
    # shop_id = fields.Many2one('amazon.shop', string=u'店铺', required=True)
    distributor = fields.Many2one('res.users', string=u'经销商', required=True,
                                  default=lambda self: self.env.user.merchant_id or self.env.user)
    supplier = fields.Many2one('res.users', string=u'供应商', required=True)
    logistics_company_id = fields.Many2one('logistics.company', string=u'物流公司')

    order_line = fields.One2many('fba.replenish.line', 'order_id', string=u'订单明细')
    # so_id = fields.Many2one('sale.order',u'订单')
    # demand_qty_ttl = fields.Float(u'需求数量', compute='_get_totals')
    # supply_qty_ttl = fields.Float(u'补货数量', compute='_get_totals')
    # dist_orders = fields.Boolean(u'本经销商的订单', compute='_if_dist_orders', search='_get_dist_orders')
    # supp_orders = fields.Boolean(u'本供应商的订单', compute='_if_supp_orders', search='_get_supp_orders')

    method = fields.Selection([
        ('sea', u'海运'),
        ('air', u'空运'),
        ('currier', u'特快'),
        ('post', u'平邮')], string=u'运输方式', required=True)
    type = fields.Selection([
        ('supplier_delivery', u'供应商代发'),
        ('other_delivery', u'第三方机构发货')
    ], string=u'发货方式', required=True)
    state = fields.Selection([
        ('draft', u'新建'),
        ('supplier', u'供应商确认'),
        ('freight', u'平台运费'),
        ('accept', u'经销商确认'),
        ('done', u'完成'),
        ('cancel', u'取消')], string=u'状态', default='draft')

    @api.model
    def create(self, val):
        if not val.get('name'):
            val['name'] = self.env['ir.sequence'].next_by_code('fba.replenish.number') or '/'
        result = super(FbaReplenish, self).create(val)
        result.check_data()
        return result

    @api.multi
    def write(self, val):
        result = super(FbaReplenish, self).write(val)
        self.check_data()
        return result

    @api.multi
    def check_data(self):
        for record in self:
            suppliers = []
            for line in record.order_line:
                suppliers.append(line.supplier)
            suppliers = list(set(suppliers))
            if len(suppliers) > 1:
                raise UserError(u'只能选择一个供应商供应商不符')
            elif len(suppliers) == 1:
                record.supplier = suppliers[0].id



class FbaReplenishLine(models.Model):
    _name = 'fba.replenish.line'

    order_id = fields.Many2one('fba.replenish', ondelete='cascade')
    product_id = fields.Many2one('product.product', domain=[('state', '=', 'platform_published')], string=u'产品')
    product_uom = fields.Many2one('product.uom', string=u'计量单位', related='product_id.uom_id', readonly=True)
    supplier = fields.Many2one('res.users', related='product_id.product_tmpl_id.merchant_id', string=u'供应商')

    need_qty = fields.Float(string=u'需求数量', digits=(16,3))
    available_qty = fields.Float(string=u'补货数量', digits=(16,3))
    platform_price = fields.Float(compute='_compute_price', store=True, readonly=True, string=u'采购单价(元)')
    supplier_price = fields.Float(compute='_compute_price', store=True, readonly=True, string=u'供货单价(元)')
    distributor_total = fields.Float(string=u'金额(元)', digits=(16, 2), compute='')
    supplier_total = fields.Float(string=u'金额(元)',digits=(16,2), compute='')

    state = fields.Selection([
        ('draft', u'新建'),
        ('wait_supplier_confirm', u'待供应商确认'),
        ('wait_platform_confirm', u'待平台确认'),
        ('wait_distributor_confirm', u'待经销商确认'),
        ('done', u'完成'),
        ('cancel', u'取消'),
    ], related='order_id.state', store=False, string=u'状态')

    @api.depends('product_id')
    def _compute_price(self):
        for record in self:
            record.platform_price = record.product_id.platform_price
            record.supplier_price = record.product_id.supplier_price




