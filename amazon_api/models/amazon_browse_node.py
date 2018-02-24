# -*- coding: utf-8 -*-

from odoo import models, fields, api, modules
from odoo.exceptions import UserError

class AmazonBrowseNode(models.Model):
    _name = "amazon.browse.node"

    name = fields.Char(string=u'名称')
    code = fields.Char(string=u'code')

    country_id = fields.Many2one('amazon.country', string=u'国家')
    parent_id = fields.Many2one('amazon.browse.node', string=u'上级类别')

    child_ids = fields.One2many('amazon.browse.node', 'parent_id', string=u'子类别')

    @api.model
    def create_browse_node(self):
        '''创建browse node'''
        node_obj = self.env['amazon.browse.node']
        path = modules.get_module_resource('amazon_api', 'data', 'browse_node_data.txt')
        with open(path, 'r') as f:
            content = f.read()
        data = eval(content)
        for val in data:
            country = self.env['amazon.country'].search([('code', '=', val.get('country_code'))])
            country_id = country.id or False
            node = node_obj.search([('name', '=', val.get('name')), ('country_id', '=', country_id)])
            if node:
                continue
            node_obj.create({
                'name': val.get('name'),
                'code': val.get('node_code'),
                'country_id': country_id
            })