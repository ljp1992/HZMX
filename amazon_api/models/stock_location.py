# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
from lxml import etree

class StockLocation(models.Model):
    _inherit = "stock.location"

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        print args,offset,limit,order,count
        context = self.env.context or {}
        if context.get('view_own_data'):
            if self.user_has_groups('b2b_platform.b2b_shop_operator'):
                args += [('partner_id', '=', self.env.user.merchant_id.partner_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_seller'):
                args += [('partner_id', '=', self.env.user.partner_id.id)]
            elif self.user_has_groups('b2b_platform.b2b_manager'):
                pass
            else:
                pass
        return super(StockLocation, self).search(args, offset, limit, order, count=count)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # print view_id,view_type,toolbar,submenu
        res = super(StockLocation, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                          submenu=submenu)
        if view_type == 'tree' and self.user_has_groups('b2b_platform.b2b_manager'):
            res['arch'] = res['arch'].replace('<tree create="0">', '<tree>')
        elif view_type == 'form' and self.user_has_groups('b2b_platform.b2b_manager'):
            res['arch'] = res['arch'].replace('<form create="0" edit="0">', '<form>')
        return res


