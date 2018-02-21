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
        'views/amazon_seller.xml',
        'views/amazon_shop.xml',
        'views/merchant_category.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/product_attribute.xml',
        'views/product_attribute_value.xml',
        'views/product_description.xml',
        'views/product_brand.xml',
        'views/freight_template.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
}