## This module developed by KGISL 

{
    "name": "Multi Payment Process",
    "summary": """Multi Invoice Payment """,
    "author": "Karthikeyan",
    "website": "https://www.bahmni.org/",
    "category": "Account",    
    "license": "LGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        'views/account_invoice_view.xml',
        'views/custom_account_payment_views.xml',
        'views/account_report.xml',
        'report/report_invoice_inherit.xml',
    ],    
    "installable": True,
    "application": True,    
    "auto_install": False,
}
