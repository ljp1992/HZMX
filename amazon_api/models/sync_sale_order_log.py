# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.addons.amazon_api.amazon_api.mws import Feeds,DictWrapper
import datetime

class SyncSaleOrderLog(models.Model):
    _name = "sync.sale.order.log"
    _rec_name = 'message'
    _order = 'id desc'

    message = fields.Char(string=u'信息')

    sync_time = fields.Datetime(default=lambda self: datetime.datetime.now(), string=u'时间')

    # shop_id = fields.Many2one('amazon.shop', string=u'店铺')
    operator_id = fields.Many2one('res.users', default=lambda self: self.env.user, string=u'操作员')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')

    order_line = fields.One2many('sync.sale.order.log.line', 'order_id')


class SyncSaleOrderLogLine(models.Model):
    _name = "sync.sale.order.log.line"
    _rec_name = 'message'

    order_num = fields.Char(string=u'单号')
    message = fields.Char(string=u'信息')

    order_id = fields.Many2one('sync.sale.order.log')


