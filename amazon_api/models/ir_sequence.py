# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from odoo.exceptions import UserError
import datetime, string

class IrSequence(models.Model):
    _inherit = "ir.sequence"

    next_sku = fields.Char(string=u'next SKU')

    @api.model
    def get_seller_sku(self):
        '''生成seller sku 10位 6位日期+4位字母 一天最多可生成456796'''
        record = self.search([('code', '=', 'sku_seq')], limit=1)
        sku = record.next_sku
        current_sku = sku[6:]
        if current_sku == 'ZZZZ':
            raise UserError(u'今日的seller sku数量达到上限！')
        now_time = datetime.datetime.now() + datetime.timedelta(hours=8)
        date_str = now_time.strftime('%y%m%d')
        if date_str == sku[:6]:
            uppercases = [word for word in string.uppercase]
            current_sku_list = [word for word in current_sku]
            reverse_seq = current_sku_list[::-1]
            for i in range(len(reverse_seq)):
                index = uppercases.index(reverse_seq[i])
                if index == 25:
                    reverse_seq[i] = 'A'
                else:
                    reverse_seq[i] = uppercases[index + 1]
                    break
            next_seq = ''
            for word in reverse_seq:
                next_seq = word + next_seq
            record.next_sku = date_str + next_seq
        else:
            record.next_sku = date_str + 'AAAB'
            return date_str + 'AAAA'
        return sku


