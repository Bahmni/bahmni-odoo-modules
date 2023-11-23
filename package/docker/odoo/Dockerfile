FROM odoo:16.0

ENV ADDON_PATH=/opt/bahmni-erp/bahmni-addons

COPY package/docker/odoo/odoo.conf /etc/odoo/odoo.conf
COPY bahmni_account ${ADDON_PATH}/bahmni_account/
COPY bahmni_api_feed ${ADDON_PATH}/bahmni_api_feed/
COPY bahmni_product ${ADDON_PATH}/bahmni_product/
COPY bahmni_purchase ${ADDON_PATH}/bahmni_purchase/
COPY bahmni_sale ${ADDON_PATH}/bahmni_sale/
COPY bahmni_stock ${ADDON_PATH}/bahmni_stock/
COPY jss_data_import ${ADDON_PATH}/jss_data_import/
COPY restful_api ${ADDON_PATH}/restful_api/

CMD ["odoo", "-u", "all", "-i", "sale_management,purchase,stock,point_of_sale,l10_generic_coa,restful_api", "--without-demo", "-d odoo"]