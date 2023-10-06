FROM postgres:16.0-alpine

COPY package/resources/database/setupDB.sql /resources/setupDB.sql
# COPY package/docker/freshDB/odoo_clean_dump.sql /resources/odoo_clean_dump.sql
COPY package/docker/freshDB/configureDB.sh /docker-entrypoint-initdb.d/configureDB.sh