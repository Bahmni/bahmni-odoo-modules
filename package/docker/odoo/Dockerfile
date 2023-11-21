FROM odoo:16.0

ENV ADDON_PATH=/opt/bahmni-erp/bahmni-addons

COPY package/docker/odoo/odoo.conf /etc/odoo/odoo.conf
COPY restful_api ${ADDON_PATH}/restful_api/

CMD ["odoo", "-u", "all", "-i", "sale_management,purchase,stock,point_of_sale,l10_generic_coa,restful_api", "--without-demo", "-d odoo"]