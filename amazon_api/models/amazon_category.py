# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AmazonCategory(models.Model):
    _name = "amazon.category"

    name = fields.Char(string=u'名称')

    parent_id = fields.Many2one('amazon.category', string=u'上级类别')



