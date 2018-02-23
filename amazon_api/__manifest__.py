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
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
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
        'views/shop_template_wizard.xml',
        'views/amazon_currency.xml',
        'views/upc_code.xml',
        'views/submission_history.xml',
        'views/sale_order.xml',
        'views/sync_sale_order.xml',
        'views/sync_sale_order_log.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
}