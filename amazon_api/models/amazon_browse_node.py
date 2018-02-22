# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class AmazonBrowseNode(models.Model):
    _name = "amazon.browse.node"

    name = fields.Char(string=u'名称')

    parent_id = fields.Many2one('amazon.browse.node', string=u'上级类别')

