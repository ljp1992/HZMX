# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import xlrd,base64,datetime

class StockAdjust(models.TransientModel):
    _name = "stock.adjust"

    data = fields.Binary(string=u'数据')

    @api.multi
    def import_stock_excel(self):
        '''库存调整'''
        self.ensure_one()
        if not self.data:
            return
        excel_obj = xlrd.open_workbook(file_contents=base64.decodestring(self.data))
        sheets = excel_obj.sheets()
        pro_obj = self.env['product.product']
        quant_obj = self.env['stock.quant']
        loc_obj = self.env['stock.location']
        merchant = self.env.user.merchant_id or self.env.user
        for sh in sheets:
            id_col = 0
            qty_col = 0
            for col in range(sh.ncols):
                if sh.cell(0, col).value == u'ID':
                    id_col = col
                elif sh.cell(0, col).value == u'在手数量':
                    qty_col = col
            for row in range(1, sh.nrows):
                product_id = int(sh.cell(row, id_col).value)
                product = pro_obj.search([('id', '=', product_id)])
                if not product:
                    raise UserError(u'Not found product!')
                if product.product_tmpl_id.merchant_id != merchant:
                    raise UserError(u'该用户没有调整产品%s库存的权限' % (product.name))
                qty = sh.cell(row, qty_col).value
                if type(qty) not in [float, int]:
                    qty = float(qty)
                supplier_loc = loc_obj.return_merchant_supplier_location(merchant)
                quant = quant_obj.sudo().search([
                    ('location_id', '=', supplier_loc.id),
                    ('product_id', '=', product_id)
                ], limit=1)
                if quant:
                    quant.qty = qty
                else:
                    quant_obj.sudo().create({
                        'product_id': product_id,
                        'location_id': supplier_loc.id,
                        'qty': qty,
                    })

    # @api.multi
    # def import_stock_excel(self):
    #     '''库存调整'''
    #     self.ensure_one()
    #     if not self.data:
    #         return
    #     excel_obj = xlrd.open_workbook(file_contents=base64.decodestring(self.data))
    #     sheets = excel_obj.sheets()
    #     inventory_obj = self.env['stock.inventory']
    #     inventory_line_obj = self.env['stock.inventory.line']
    #     pro_obj = self.env['product.product']
    #     quant_obj = self.env['stock.quant']
    #     loc_obj = self.env['stock.location']
    #     if not self.user_has_groups('b2b_platform.b2b_seller'):
    #         raise UserError(u'该用户没有权限调整库存！')
    #     merchant = self.env.user
    #     for sh in sheets:
    #         id_col = 0
    #         qty_col = 0
    #         for col in range(sh.ncols):
    #             if sh.cell(0, col).value == u'ID':
    #                 id_col = col
    #             elif sh.cell(0, col).value == u'在手数量':
    #                 qty_col = col
    #         for row in range(1, sh.nrows):
    #             product_id = int(sh.cell(row, id_col).value)
    #             product = pro_obj.browse(product_id)
    #             if self.user_has_groups('b2b_platform.b2b_seller') and product.merchant_id != merchant:
    #                 raise UserError(u'该用户没有调整产品%s库存的权限' % (product.name))
    #             qty = sh.cell(row, qty_col).value
    #             if type(qty) not in [float, int]:
    #                 qty = float(qty)
    #             location = loc_obj.sudo().search([
    #                 ('location_id', '=', self.env.ref('b2b_platform.supplier_stock').id),
    #                 ('partner_id', '=', self.env.user.partner_id.id),
    #             ])
    #             inventory = inventory_obj.create({
    #                 'location_id': location.id,
    #                 'company_id': 1,
    #                 'state': 'draft',
    #                 'name': product.name,
    #                 'product_id': product.id,
    #                 'filter': 'product',
    #                 'accounting_date': fields.Date.today(),
    #             })
    #             inventory_line = inventory_line_obj.create({
    #                 'inventory_id': inventory.id,
    #                 'product_qty': qty,
    #                 'location_name': location.name,
    #                 'location_id': location.id,
    #                 'company_id': 1,
    #                 'product_id': product.id,
    #                 'product_name': product.name,
    #                 'product_uom_id': product.uom_id.id,
    #             })
    #             quant_rec = quant_obj.sudo().search([
    #                 ('location_id', '=', location.id),
    #                 ('product_id', '=', product.id)
    #             ])
    #             theoretical_qty = sum([x.qty for x in quant_rec])
    #             inventory_line.write({'theoretical_qty': theoretical_qty})
    #             inventory.action_done()
    #
    #             quants = quant_obj.sudo().search([
    #                 ('location_id', '=', location.id),
    #                 ('owner_id', '=', False)
    #             ])
    #             if quants:
    #                 quants.write({'owner_id': merchant.partner_id.id})

