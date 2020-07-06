# -*- coding: utf-8 -*-
# Copyright (C) 2013-Today  Carlos Eduardo Vercelino - CLVsol
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from functools import reduce

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % reduce(lambda ll, b: divmod(ll[0], b) + ll[1:], [(t * 1000,), 1000, 60, 60])


class VerificationBatchExec(models.TransientModel):
    _description = 'Verification Batch Exec'
    _name = 'clv.verification.batch.exec'

    def _default_batch_ids(self):
        return self._context.get('active_ids')
    batch_ids = fields.Many2many(
        comodel_name='clv.verification.batch',
        relation='clv_verification_batch_exec_rel',
        string='Batchs to Execute',
        default=_default_batch_ids)
    count_batches = fields.Integer(
        string='Number of Batchs',
        compute='_compute_count_batches',
        store=False
    )

    @api.depends('batch_ids')
    def _compute_count_batches(self):
        for r in self:
            r.count_batches = len(r.batch_ids)

    def _reopen_form(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }
        return action

    def do_verification_batch_exec(self):
        self.ensure_one()

        from time import time
        start_total = time()

        verification_log = False

        for batch in self.batch_ids:

            _logger.info(u'%s %s', '>>>>>', batch.name)

            if verification_log is False:
                verification_log = '########## ' + batch.name + ' ##########\n'
            else:
                verification_log += '\n########## ' + batch.name + ' ##########\n'

            for verification_batch_member in batch.verification_batch_member_ids:

                if verification_batch_member.enabled:

                    start = time()

                    schedule = verification_batch_member.ref_id

                    _logger.info(u'%s %s', '>>>>>', schedule.name)

                    model = schedule.model
                    _logger.info(u'%s %s [%s]', '>>>>>', schedule.name, model)

                    items = False
                    if (schedule.verify_all_items is False) and \
                       (schedule.verification_set_elements is False) and \
                       (schedule.model_items is not False):
                        items = eval('schedule.' + schedule.model_items)
                    elif (schedule.verify_all_items is False) and \
                         (schedule.verification_set_elements is True) and \
                         (schedule.verification_set_id is not False):
                        set_elements = schedule.verification_set_id.set_element_ids
                        items = []
                        for set_element in set_elements:
                            items.append(set_element.ref_id)
                    elif schedule.verify_all_items is True:
                        Model = schedule.env[schedule.model]
                        items = Model.search(eval(schedule.verification_domain_filter))

                    _logger.info(u'%s %s %s', '>>>>>>>>>>', items, schedule.method)

                    if len(items) > 0:

                        method_call = False
                        if schedule.method is not False:
                            method_call = 'items.' + schedule.method + '()'
                            _logger.info(u'%s %s %s', '>>>>>>>>>>', schedule.method, method_call)

                        if method_call:

                            schedule.verification_log = 'method: ' + str(schedule.method) + '\n\n'
                            schedule.verification_log +=  \
                                'items: ' + str(len(items)) + '\n\n'

                            exec(method_call)

                            schedule.verification_log +=  \
                                '\nExecution time: ' + str(secondsToStr(time() - start)) + '\n'

                            verification_log += '\n########## ' + schedule.name + ' ##########\n'
                            verification_log += schedule.verification_log

                            self.env.cr.commit()

            verification_log += '\n############################################################'
            verification_log +=  \
                '\nExecution time: ' + str(secondsToStr(time() - start_total)) + '\n'

            batch.verification_log = verification_log

            _logger.info(u'%s %s', '>>>>> Execution time: ', secondsToStr(time() - start_total))

        return True
        # return self._reopen_form()
