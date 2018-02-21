# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

active_attr =  [
    {'amazon_attr': 'Color', 'odoo_attr': u'颜色'},
    {'amazon_attr': 'Size', 'odoo_attr': u'尺寸'},
    {'amazon_attr': 'Capacity', 'odoo_attr': u'容量'},
    {'amazon_attr': 'Design', 'odoo_attr': u'设计'},
    {'amazon_attr': 'Edition', 'odoo_attr': u'版本'},
    {'amazon_attr': 'Flavor', 'odoo_attr': u'口味'},
    {'amazon_attr': 'Material', 'odoo_attr': u'材料'},
    {'amazon_attr': 'Pattern', 'odoo_attr': u'图案'},
    {'amazon_attr': 'Shape', 'odoo_attr': u'形状'},
    {'amazon_attr': 'Scent', 'odoo_attr': u'气味'},
    # {'amazon_attr': 'Shape', 'odoo_attr': u'样式'},
    {'amazon_attr': 'UnitCount', 'odoo_attr': u'单位数'},
    {'amazon_attr': 'Wattage', 'odoo_attr': u'瓦数'},
    {'amazon_attr': 'Weight', 'odoo_attr': u'重量'},

]

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'
    _order = "id asc"

    english_name = fields.Char(string=u'英文名称')

    @api.model
    def create_product_attribute(self):
        '''根据亚马逊属性及属性值，创建odoo属性及属性值'''
        odoo_attr_obj = self.env['product.attribute']
        for attr in active_attr:
            odoo_attr_name = attr['odoo_attr']
            amazon_attr_name = attr['amazon_attr']
            odoo_attr = odoo_attr_obj.search([
                ('name', '=', odoo_attr_name),
                ('english_name', '=', amazon_attr_name),
            ], limit=1)
            if not odoo_attr:
                odoo_attr_obj.create({
                    'name': odoo_attr_name,
                    'english_name': amazon_attr_name,
                })


