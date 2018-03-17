# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.osv import osv
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class BulletPoint(models.Model):
    _name = 'bullet.point'

    name = fields.Char(required=True, string=u'卖点')

    description_id = fields.Many2one('product.description')

