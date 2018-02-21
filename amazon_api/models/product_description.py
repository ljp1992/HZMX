# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class ProductDescription(models.Model):
    _name = 'product.description'

    title = fields.Char(string=u'产品标题')
    keyword = fields.Char(string=u'关键词')

    short_description = fields.Text(string=u'重点说明')
    detail_description = fields.Text(string=u'详细描述')

    lang_id = fields.Many2one('amazon.lang', string=u'语言')
    template_id = fields.Many2one('product.template', string=u'产品')