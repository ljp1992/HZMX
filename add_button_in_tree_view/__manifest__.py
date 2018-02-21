# -*- coding: utf-8 -*-
{
    'name': "tree视图添加导入按钮",

    'summary': """
        """,

    'description': """
    """,

    'author': "青岛欧度软件技术有限责任公司",
    'website': "http://www.qdodoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','base_import','web'],

    # always loaded
    'data': [
        'views/load_js.xml',
        # 'views/excel_template.xml',
        'wizard/wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'qweb':[
        # 'static/src/xml/import.xml',
    ],
    'application': False,
}