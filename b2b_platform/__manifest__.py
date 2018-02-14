# -*- coding: utf-8 -*-
{
    'name': "b2b_platform",

    'summary': """
        """,

    'description': """
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'sale', 'purchase', 'account'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        # 'security/ir.model.access.csv',
        'views/menu.xml',
        'views/res_users.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'application': True,
}