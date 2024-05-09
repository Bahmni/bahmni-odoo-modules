## This module developed by KGISL

{
    "name": "Bahmni Auto Payment Reconciliation",
    "summary": """This module extends the Customer payment functionality to allocate the payment amount automatically across multiple open invoices """,
    "author": "Karthikeyan",
    "website": "https://www.bahmni.org/",
    "category": "Accounting",
    "license": "LGPL-3",
    "depends": ["account","bahmni_sale"],
    "data": [
        "security/ir.model.access.csv",
        'views/account_payment_view_inherit.xml',
        'views/res_config_inherit.xml',
        'views/account_report.xml',
        'report/report_invoice_inherit.xml',
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
