# -*- coding: utf-8 -*-
# © 2018 Halltic eSolutions S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action


class AmazonBinding(models.AbstractModel):
    """ Abstract Model for the Bindings.

    All the models used as bindings between Amazon and Odoo
    (``amazon.res.partner``, ``amazon.product.product``, ...) should
    ``_inherit`` it.
    """
    _name = 'amazon.binding'
    _inherit = 'external.binding'
    _description = 'Amazon Binding (abstract)'

    # odoo_id = odoo-side id must be declared in concrete model
    backend_id = fields.Many2one(
        comodel_name='amazon.backend',
        string='Amazon Backend',
        required=True,
        ondelete='restrict',
    )
    # fields.Char because 0 is a valid Amazon ID
    external_id = fields.Char(string='ID on Amazon')

    _sql_constraints = [
        ('amazon_uniq', 'unique(backend_id, external_id)',
         'A binding already exists with the same Amazon ID.'),
    ]

    @job(default_channel='root.amazon')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of records modified on Amazon """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.amazon')
    @api.model
    def import_record(self, backend, external_id, force=False):
        """ Import a Amazon record """
        with backend.work_on(self._name) as work:
            importer = work.component(usage='record.importer')
            return importer.run(external_id, force=False)

    @job(default_channel='root.amazon')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def export_record(self, fields=None):
        """ Export a record on Amazon """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

    @job(default_channel='root.amazon')
    @related_action(action='related_action_amazon_link')
    def export_delete_record(self, backend, external_id):
        """ Delete a record on Amazon """
        with backend.work_on(self._name) as work:
            deleter = work.component(usage='record.exporter.deleter')
            return deleter.run(external_id)
