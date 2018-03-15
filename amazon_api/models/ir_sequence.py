# -*- encoding: utf-8 -*-

from openerp import models, fields, api, _
from odoo.exceptions import UserError
import datetime, string, re

class IrSequence(models.Model):
    _inherit = "ir.sequence"

    next_sku = fields.Char(string=u'next SKU')
    last_num = fields.Char(string=u'上一个编号')

    @api.model
    def get_next_tmpl_system_code(self):
        '''获取下一个产品的系统编号 编码格式为 xxBxxMxxTxx'''
        record = self.search([('code', '=', 'system_code_seq')], limit=1)
        if not record:
            raise UserError(u'Not found system_code_seq!')
        try:
            search_obj = re.match(r'(.*?)B(.*?)M(.*?)T(.*)', record.last_num)
        except Exception, e:
            raise UserError(str(e))
        billion = int(search_obj.group(1))
        million = int(search_obj.group(2))
        thousand = int(search_obj.group(3))
        unit = int(search_obj.group(4))
        unit += 1
        if unit == 1000:
            unit = 0
            thousand += 1
            if thousand == 1000:
                thousand = 0
                million += 1
                if million ==1000:
                    million = 0
                    billion += 1
        new_code = u'%dB%dM%dT%d' % (billion, million, thousand, unit)
        record.last_num = new_code
        print new_code
        return new_code

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


