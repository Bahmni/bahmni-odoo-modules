/** @odoo-module */

import { _lt } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

const { Component } = owl;

export class PdfOptionsModal extends Component {
}

PdfOptionsModal.components = { Dialog }
PdfOptionsModal.template = "report_pdf_options.ButtonOptions";
