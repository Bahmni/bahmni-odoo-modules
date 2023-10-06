FROM odoo:16

ENV ADDON_PATH=/opt/bahmni-erp/bahmni-addons
COPY package/docker/odoo/odoo.conf /etc/odoo/odoo.conf
CMD ["odoo", "-u", "all"]