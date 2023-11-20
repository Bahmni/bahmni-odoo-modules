# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
import json
import uuid

STATE_CODE_PREFIX = 'UNKNOWN-'
_logger = logging.getLogger(__name__)


class ApiEventWorker(models.Model):
    _name = 'api.event.worker'
    _auto = False

    @api.model
    def process_event(self, vals):
        '''Method getting triggered from Bahmni side'''
        _logger.info("vals")
        _logger.info(vals)
        category = vals.get("category")
        try:
            if category == "create.sale.order":
                self.env['order.save.service'].create_orders(vals)
                return "The Service order have been successfully created / updated."
            else:
                return "Integration process is not defined. Kindly contact ERP tech team for support."
        except Exception as err:
            _logger.info("\n Processing event threw error: %s", err)
            raise

