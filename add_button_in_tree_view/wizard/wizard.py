# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import xlrd,base64,datetime


class ImportWizard(models.TransientModel):
    _name = 'import.wizard'

    name = fields.Char(default=u'导入excel', string=u'')
    data = fields.Binary(string=u'文件')

    # 数据导入
    @api.multi
    def import_excel(self):
        if self.data:
            excel_obj = xlrd.open_workbook(file_contents=base64.decodestring(self.data))
            sheets = excel_obj.sheets()
            upc_obj = self.env['upc.code']
            product_obj = self.env['product.product']
            for sh in sheets:
                for row in range(0, sh.nrows):
                    code = sh.cell(row, 0).value
                    code = code.replace(' ', '')
                    if type(code) is not unicode:
                        raise UserError(u'%s 编码必须为文本类型，不能为数字格式' % code)
                    result = upc_obj.sudo().search([('name', '=', code)])
                    if result:
                        continue
                    product = product_obj.sudo().search([('upc', '=', code)])
                    if product:
                        continue
                    upc_obj.create({'name': code})
        return {
            'name': u'UPC编码',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'upc.code',
        }


