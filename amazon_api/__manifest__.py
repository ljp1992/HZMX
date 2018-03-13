# -*- coding: utf-8 -*-
{
    'name': "amazon_api",

    'summary': """
       """,

    'description': """
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'b2b_platform'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        'views/load_js.xml',
        'views/amazon_seller.xml',
        'views/amazon_shop.xml',
        'views/product_category.xml',
        'views/merchant_category.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/product_attribute.xml',
        'views/product_attribute_value.xml',
        'views/product_description.xml',
        'views/product_brand.xml',
        'views/freight_template.xml',
        'views/shop_template.xml',
        'views/amazon_currency.xml',
        'views/upc_code.xml',
        'views/submission_history.xml',
        'views/sale_order.xml',
        'views/sync_sale_order_log.xml',
        'views/purchase_order.xml',
        'views/stock_picking.xml',
        'views/stock_location.xml',
        'views/logistics_company.xml',
        'views/stock_pack_operation.xml',
        'views/stock_quant.xml',
        'views/fba_replenish.xml',
        'views/transaction_detail.xml',
        'views/supplier_settlement.xml',
        'views/res_users.xml',
        'views/account_charge.xml',
        'views/account_cash.xml',
        'views/invoice.xml',
        'views/appeal_order.xml',
        'views/replenish_order.xml',
        'views/sync_product.xml',
        'views/fetchmail_server_inbox.xml',

        'wizard_views/shop_template_wizard.xml',
        'wizard_views/amazon_wizard.xml',
        'wizard_views/stock_adjust.xml',
        'wizard_views/sync_sale_order.xml',
        'wizard_views/stock_immediate_transfer.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
}