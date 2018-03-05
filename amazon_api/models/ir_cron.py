# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import datetime

class IrCron(models.Model):
    _inherit = 'ir.cron'

    def initial_data(self):
        '''初始化数据。创建亚马逊市场数据、产品属性、亚马逊模板、variation theme、browse node'''
        self.env['amazon.marketplace'].maintain_amazon_marketplace()
        self.env['product.attribute'].create_attribute_and_categs()
        self.env['amazon.category'].create_categs_theme()
        self.env['amazon.browse.node'].create_browse_node()
        self.env['b2b.account'].create_account() # 创建账户
        return

    def handle_history_data(self):
        '''历史数据处理'''

        return