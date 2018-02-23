# -*- coding: utf-8 -*-

from odoo import models, fields, api, modules
from odoo.exceptions import UserError

class AmazonCategory(models.Model):
    _name = "amazon.category"

    name = fields.Char(string=u'名称')

    parent_id = fields.Many2one('amazon.category', string=u'父模板')

    child_ids = fields.One2many('amazon.category', 'parent_id', string=u'子模板')
    theme_ids = fields.One2many('variation.theme', 'categ_id')

    attribute_ids = fields.Many2many('product.attribute', 'attribute_amazon_categ_rel', 'categ_id', 'attr_id',
                                        string=u'亚马逊模板')

    @api.multi
    def name_get(self):
        result = []
        for categ in self:
            name = categ.name
            if categ.parent_id:
                name = categ.parent_id.name + '/' + name
            result.append((categ.id, name))
        return result

    @api.model
    def create_categs_theme(self):
        '''创建亚马逊模板和variation theme'''
        theme_obj = self.env['variation.theme']
        path = modules.get_module_resource('amazon_api', 'data', 'categ_theme_data.txt')
        with open(path, 'r') as f:
            content = f.read()
        data = eval(content)
        categs = self.env['amazon.category'].sudo().search([])
        for categ in categs:
            if not data.has_key(categ.name):
                continue
            theme_names = data[categ.name]
            for theme_name in theme_names:
                theme = theme_obj.search([('categ_id', '=', categ.id), ('name', '=', theme_name)])
                if not theme:
                    theme_obj.create({'name': theme_name, 'categ_id': categ.id})



