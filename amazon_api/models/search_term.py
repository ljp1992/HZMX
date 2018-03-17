# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class SearchTerm(models.Model):
    _name = 'search.term'

    name = fields.Char(required=True, string=u'关键词')

    description_id = fields.Many2one('product.description')
