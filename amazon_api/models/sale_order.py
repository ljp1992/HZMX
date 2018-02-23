# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    e_order = fields.Char(string=u'电商订单号')

    sale_date = fields.Datetime(string=u'下单日期')
    confirm_date = fields.Datetime(string=u'确认日期')

    e_order_amount = fields.Float(string=u'订单金额')
    e_order_freight = fields.Float(string=u'运费')
    e_order_commission = fields.Float(string=u'佣金')

    shop_id = fields.Many2one('amazon.shop', string=u'店铺')
    e_currency_id = fields.Many2one('amazon.currency', related='shop_id.currency_id', string=u'币种')
    operator_id = fields.Many2one('res.users', default=lambda self: self.env.user, string=u'操作员')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')
    amazon_country_id = fields.Many2one('amazon.country', related='shop_id.country_id', string=u'国家')


    platform = fields.Selection([
        ('amazon', u'亚马逊'),
        ('ebay', u'Ebay')], default='amazon', string=u'来源平台')
    delivery_mode = fields.Selection([
        ('MFN', u'自发货'),
        ('FBA', u'FBA')], default='MFN', string=u'运输方式')
    amazon_state = fields.Selection([
        ('PendingAvailability', u'PendingAvailability'),
        ('Pending', u'Pending'),
        ('Unshipped', u'Unshipped'),
        ('PartiallyShipped', u'PartiallyShipped'),
        ('Shipped', u'Shipped'),
        ('InvoiceUnconfirmed', u'InvoiceUnconfirmed'),
        ('Canceled', u'Canceled'),
        ('Unfulfillable', u'Unfulfillable'),
    ], string=u'亚马逊订单状态')


