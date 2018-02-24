# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class CopyPlatform(models.Model):
    _name = "copy.platform"

    name = fields.Char(required=True, string=u'名称')

    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                              string=u'商户')