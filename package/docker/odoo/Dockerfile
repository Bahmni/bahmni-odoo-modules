FROM odoo:16.0

ENV ADDON_PATH=/opt/bahmni-erp/bahmni-addons

COPY package/docker/odoo/odoo.conf /etc/odoo/odoo.conf
COPY bahmni_account ${ADDON_PATH}/bahmni_account/
COPY bahmni_address_mapping ${ADDON_PATH}/bahmni_address_mapping/
COPY bahmni_api_feed ${ADDON_PATH}/bahmni_api_feed/
COPY bahmni_initializer ${ADDON_PATH}/bahmni_initializer/
COPY bahmni_product ${ADDON_PATH}/bahmni_product/
COPY bahmni_purchase ${ADDON_PATH}/bahmni_purchase/
COPY bahmni_sale ${ADDON_PATH}/bahmni_sale/
COPY bahmni_stock ${ADDON_PATH}/bahmni_stock/
COPY restful_api ${ADDON_PATH}/restful_api/
COPY community_modules/base_account_budget ${ADDON_PATH}/base_account_budget/
COPY community_modules/base_accounting_kit ${ADDON_PATH}/base_accounting_kit/
COPY openerp7_data_import ${ADDON_PATH}/openerp7_data_import/
COPY package/resources/data/address.seed.csv ${ADDON_PATH}/bahmni_initializer/data/
COPY bahmni_reports ${ADDON_PATH}/bahmni_reports

RUN pip3 install python-decouple

CMD ["odoo", "-u", "all", "-i", "sale_management,purchase,stock,point_of_sale,l10n_generic_coa,bahmni_account,bahmni_product,bahmni_api_feed,bahmni_stock,bahmni_purchase,bahmni_address_mapping,bahmni_sale,restful_api,bahmni_reports", "--without-demo", "-d odoo"]
