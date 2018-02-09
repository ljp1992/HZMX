# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AmazonSeller(models.Model):
    _name = "amazon.seller"

    name = fields.Char(string=u'名称', required=True)
    access_key = fields.Char(string='访问密钥', required=True)
    secret_key = fields.Char(string=u'密钥', required=True)
    merchant_id = fields.Char(string=u'商家ID', required=True)
