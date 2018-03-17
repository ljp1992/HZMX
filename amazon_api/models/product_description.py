# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductDescription(models.Model):
    _name = 'product.description'

    title = fields.Char(required=True, string=u'产品标题')

    detail_description = fields.Text(string=u'详细描述')

    lang_id = fields.Many2one('amazon.lang', required=True, string=u'语言')
    template_id = fields.Many2one('product.template', string=u'产品')

    search_terms = fields.One2many('search.term', 'description_id', string=u'关键词')
    bullet_points = fields.One2many('bullet.point', 'description_id', string=u'卖点描述')
