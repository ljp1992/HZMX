# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class MerchantCategory(models.Model):
    _name = "merchant.category"

    name = fields.Char(inverse='_set_display_name', required=True, string=u'分类名称')
    display_name = fields.Char(store=True, string=u'分类名称')

    rate = fields.Float(string=u'上浮率(%)')

    parent_id = fields.Many2one('merchant.category', string=u'上级分类')
    merchant_id = fields.Many2one('res.users', default=lambda self: self.env.user.merchant_id or self.env.user,
                                  string=u'商户')

    child_ids = fields.One2many('merchant.category', 'parent_id')

    @api.multi
    def _get_display_name(self):
        for categ in self:
            name = categ.name
            parent = categ.parent_id
            while True:
                if parent:
                    name = parent.name + '/' + name
                    parent = parent.parent_id
                else:
                    break
            categ.display_name = name

    @api.multi
    def _set_display_name(self):
        for categ in self:
            categ._get_display_name()
            children = categ.child_ids
            if children:
                children._set_display_name()

    @api.model
    def return_act_view(self):
        domain = []
        user = self.env.user
        if user.merchant_id:
            merchant = user.merchant_id
        else:
            merchant = user
        if user.user_type in ['operator', 'merchant']:
            domain = [('merchant_id', '=', merchant.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': u'商户内部分类',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(self.env.ref('amazon_api.merchant_category_tree').id, 'tree'),
                      (self.env.ref('amazon_api.merchant_category_form').id, 'form')],
            'res_model': 'merchant.category',
            'domain': domain,
            'context': {'default_merchant_id': merchant.id},
            'target': 'current',
        }


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += ('name', operator, name)
        context = self.env.context
        if context.get('categ_id_ljp'):
            args.append(('id', '!=', int(context.get('categ_id_ljp'))))
        user = self.env.user
        if user.user_type == 'operator':
            args.append(('merchant_id', '=', user.merchant_id.id))
        elif user.user_type == 'merchant':
            args.append(('merchant_id', '=', user.id))
        result = self.search(args, limit=limit)
        return result.name_get()

    @api.multi
    def name_get(self):
        result = []
        for categ in self:
            categ_id = categ.id
            name = categ.name
            while True:
                if categ.parent_id:
                    name = categ.parent_id.name + '/' + name
                    categ = categ.parent_id
                else:
                    break
            result.append((categ_id, name))
        return result

    @api.model
    def create(self, val):
        categ = super(MerchantCategory, self).create(val)
        if val.has_key('parent_id'):
            categ.check_data()
        return categ

    @api.multi
    def write(self, val):
        result = super(MerchantCategory, self).write(val)
        if val.has_key('parent_id'):
            self.check_data()
        return result

    @api.multi
    def check_data(self):
        for categ in self:
            parent = categ.parent_id
            while True:
                if parent:
                    if parent == categ:
                        raise UserError(u'禁止创建循环类别！')
                    parent = parent.parent_id
                else:
                    break