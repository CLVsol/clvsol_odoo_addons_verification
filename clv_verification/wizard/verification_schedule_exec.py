# -*- coding: utf-8 -*-
# Copyright (C) 2013-Today  Carlos Eduardo Vercelino - CLVsol
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


def secondsToStr(t):
    return "%d:%02d:%02d.%03d" % reduce(lambda ll, b: divmod(ll[0], b) + ll[1:], [(t * 1000,), 1000, 60, 60])


class VerificationScheduleExec(models.TransientModel):
    _description = 'Verification Schedule Exec'
    _name = 'clv.verification.schedule.exec'

    def _default_schedule_ids(self):
        return self._context.get('active_ids')
    schedule_ids = fields.Many2many(
        comodel_name='clv.verification.schedule',
        relation='clv_verification_schedule_exec_rel',
        string='Schedules to Execute',
        default=_default_schedule_ids)
    count_schedules = fields.Integer(
        string='Number of Schedules',
        compute='_compute_count_schedules',
        store=False
    )

    # @api.multi
    @api.depends('schedule_ids')
    def _compute_count_schedules(self):
        for r in self:
            r.count_schedules = len(r.schedule_ids)

    # @api.multi
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

    # @api.multi
    def do_verification_schedule_exec(self):
        self.ensure_one()

        for schedule in self.schedule_ids:

            model = schedule.model
            _logger.info(u'%s %s [%s]', '>>>>>', schedule.name, model)

            method_call = False
            action_call = False
            if schedule.method is not False:
                method_call = 'self.env["clv.verification.outcome"].' + schedule.method + '(schedule)'
                _logger.info(u'%s %s %s', '>>>>>>>>>>', schedule.method, method_call)
            elif schedule.action is not False:
                action_call = 'self.env["clv.verification.outcome"].' + schedule.action + '(schedule)'
                _logger.info(u'%s %s %s', '>>>>>>>>>>', schedule.action, action_call)

            if method_call:

                schedule.verification_log = 'method: ' + str(schedule.method) + '\n\n'
                # schedule.verification_log +=  \
                #     'verification_last_update_args: ' + str(schedule.verification_last_update_args()) + '\n\n'

                exec(method_call)

            elif action_call:

                schedule.verification_log = 'action: ' + str(schedule.action) + '\n\n'
                # schedule.verification_log +=  \
                #     'verification_last_update_args: ' + str(schedule.verification_last_update_args()) + '\n\n'

                exec(action_call)

        return True
        # return self._reopen_form()
