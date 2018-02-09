# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonMarketplace(models.Model):
    _name = "amazon.marketplace"

    name = fields.Char(string=u'名称', required=True)
    code = fields.Char(required=True)
