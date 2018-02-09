# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AmazonShop(models.Model):
    _name = "amazon.shop"

    name = fields.Char(string=u'名称', required=True)

    seller_id = fields.Many2one('amazon.seller', string='站点', required=True)
    marketplace_id = fields.Many2one('amazon.marketplace', string=u'市场', required=True)
