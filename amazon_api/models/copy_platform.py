# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class CopyPlatform(models.Model):
    _name = "copy.platform"

    name = fields.Char(required=True, string=u'名称')
