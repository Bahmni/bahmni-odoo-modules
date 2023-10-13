FROM postgres:16.0-alpine

# ADD https://github.com/Bahmni/bahmni-scripts/blob/master/demo/db-backups/v0.92/odoo_backup.sql.gz?raw=true /resources/
# RUN gunzip /resources/odoo_backup.sql.gz && chmod +rx /resources/*.sql && rm -f /resources/odoo_backup.sql.gz
COPY package/resources/database/setupDB.sql /resources/setupDB.sql
COPY package/docker/demoDB/configureDemoDB.sh /docker-entrypoint-initdb.d/configureDemoDB.sh