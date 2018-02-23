# -*- coding: utf-8 -*-

from odoo import models, fields, api, modules
from odoo.exceptions import UserError

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'
    _order = "id asc"

    english_name = fields.Char(string=u'英文名称')

    amazon_categ_ids = fields.Many2many('amazon.category', 'attribute_amazon_categ_rel', 'attr_id', 'categ_id',
                                        string=u'亚马逊模板')

    @api.model
    def create_attribute_and_categs(self):
        '''创建属性和亚马逊模板'''
        attr_obj = self.env['product.attribute']
        categ_obj = self.env['amazon.category']
        path = modules.get_module_resource('amazon_api', 'data', 'attr_categ_data.txt')
        with open(path, 'r') as f:
            content = f.read()
        data = eval(content)
        for val in data:
            attr = attr_obj.search([('name', '=', val.get('name')), ('english_name', '=', val.get('amazon_name'))])
            if not attr:
                attr = attr_obj.create({'name': val.get('name'), 'english_name': val.get('amazon_name')})
            categ_ids = []
            for categ_val in val.get('categs'):
                if categ_val.get('parent_id'):
                    parent_categ = categ_obj.search([('name', '=', categ_val.get('parent_id'))])
                    if not parent_categ:
                        parent_categ = categ_obj.create({'name': categ_val.get('parent_id')})
                    categ = categ_obj.search([('name', '=', categ_val.get('categ'))])
                    if not categ:
                        categ = categ_obj.create({'name': categ_val.get('categ'), 'parent_id': parent_categ.id})
                    categ_ids.append(categ.id)
                else:
                    categ = categ_obj.search([('name', '=', categ_val.get('categ'))])
                    if not categ:
                        categ = categ_obj.create({'name': categ_val.get('categ')})
                    categ_ids.append(categ.id)
            attr.amazon_categ_ids = [(6, False, categ_ids)]

