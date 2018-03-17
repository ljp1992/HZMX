# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime
from odoo.addons.amazon_api.amazon_api.mws import Feeds

class ModifyHandleDays(models.TransientModel):
    _name = "modify.handle.days"

    handle_days = fields.Integer(default=3, string=u'处理天数')

    @api.multi
    def modify_handle_days(self):
        '''批量修改处理天数'''
        self.ensure_one()
        context = self.env.context or {}
        active_ids = context.get('active_ids', [])
        if not active_ids:
            raise UserError(u'没有选中产品！')
        tmpls = self.env['product.template'].search([('id', 'in', active_ids)])
        tmpls.write({'handle_days': self.handle_days})
