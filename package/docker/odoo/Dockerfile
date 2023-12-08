FROM odoo:16.0

ENV ADDON_PATH=/opt/bahmni-erp/bahmni-addons

COPY package/docker/odoo/odoo.conf /etc/odoo/odoo.conf
COPY bahmni_account ${ADDON_PATH}/bahmni_account/
COPY bahmni_api_feed ${ADDON_PATH}/bahmni_api_feed/
COPY bahmni_product ${ADDON_PATH}/bahmni_product/
COPY bahmni_purchase ${ADDON_PATH}/bahmni_purchase/
COPY bahmni_sale ${ADDON_PATH}/bahmni_sale/
COPY bahmni_stock ${ADDON_PATH}/bahmni_stock/
COPY restful_api ${ADDON_PATH}/restful_api/

RUN pip3 install python-decouple

CMD ["odoo", "-u", "all", "-i", "sale_management,purchase,stock,point_of_sale,l10n_generic_coa,bahmni_account,bahmni_product,bahmni_sale,bahmni_stock,bahmni_purchase,bahmni_api_feed,restful_api", "--without-demo", "-d odoo"]