# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonLang(models.Model):
    _name = "amazon.lang"

    name = fields.Char(string=u'语言')
