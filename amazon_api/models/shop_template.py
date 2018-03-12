# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ShopTemplate(models.Model):
    _name = "shop.template"

    name = fields.Char(required=True, string=u'名称')
    manufacturer = fields.Char(related='brand_id.manufacturer', string=u'制造商')
    prefix = fields.Char(string=u'品名前缀')
    suffix = fields.Char(string=u'品名后缀')
    keywords = fields.Char(string=u'关键字')

    handle_days = fields.Integer(default=3, string=u'处理天数')

    important_description = fields.Text(string=u'重要说明')
    key_description = fields.Text(string=u'要点说明')
    prefix_description = fields.Text(string=u'产品描述前缀')
    suffix_description = fields.Text(string=u'产品描述后缀')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user)
    browse_node_id = fields.Many2one('amazon.browse.node', string=u'产品分类')
    categ_id = fields.Many2one('amazon.category', string=u'亚马逊分类')
    brand_id = fields.Many2one('product.brand', string=u'品牌')
    shop_id = fields.Many2one('amazon.shop', string=u'店铺')


