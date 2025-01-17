# -*- coding: utf-8 -*-
# Copyright 2012 Dag Wieers <dag@wieers.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import os
import smtplib
import json
from ansible.plugins.callback import CallbackBase

def mail(subject='Ansible error mail', sender=None, to=None, cc=None, bcc=None, body=None, smtphost=None):

    if sender is None:
        sender='<root>'
    if to is None:
        to='root'
    if smtphost is None:
        smtphost=os.getenv('SMTPHOST', 'localhost')

    if body is None:
        body = subject

    smtp = smtplib.SMTP(smtphost)

    content = 'From: %s\n' % sender
    content += 'To: %s\n' % to
    if cc:
        content += 'Cc: %s\n' % cc
    content += 'Subject: %s\n\n' % subject
    content += body

    addresses = to.split(',')
    if cc:
        addresses += cc.split(',')
    if bcc:
        addresses += bcc.split(',')

    for address in addresses:
        smtp.sendmail(sender, address, content)

    smtp.quit()


class CallbackModule(CallbackBase):
    """
    This Ansible callback plugin mails errors to interested parties.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'mail'

    def v2_runner_on_failed(self, res, ignore_errors=False):

        host = res._host.get_name()

        if ignore_errors:
            return
        sender = '"Ansible: %s" <root>' % host
        attach = "%s:  %s" % (res._result['invocation']['module_name'], json.dumps(res._result['invocation']['module_args']))
        subject = 'Failed: %s' % attach
        body = 'The following task failed for host ' + host + ':\n\n%s\n\n' % attach

        if 'stdout' in res._result.keys() and res._result['stdout']:
            subject = res._result['stdout'].strip('\r\n').split('\n')[-1]
            body += 'with the following output in standard output:\n\n' + res._result['stdout'] + '\n\n'
        if 'stderr' in res._result.keys() and res._result['stderr']:
            subject = res['stderr'].strip('\r\n').split('\n')[-1]
            body += 'with the following output in standard error:\n\n' + res._result['stderr'] + '\n\n'
        if 'msg' in res._result.keys() and res._result['msg']:
            subject = res._result['msg'].strip('\r\n').split('\n')[0]
            body += 'with the following message:\n\n' + res._result['msg'] + '\n\n'
        body += 'A complete dump of the error:\n\n' + self._dump_results(res._result)
        mail(sender=sender, subject=subject, body=body)

    def v2_runner_on_unreachable(self, result):

        host = result._host.get_name()
        res = result._result

        sender = '"Ansible: %s" <root>' % host
        if isinstance(res, basestring):
            subject = 'Unreachable: %s' % res.strip('\r\n').split('\n')[-1]
            body = 'An error occurred for host ' + host + ' with the following message:\n\n' + res
        else:
            subject = 'Unreachable: %s' % res['msg'].strip('\r\n').split('\n')[0]
            body = 'An error occurred for host ' + host + ' with the following message:\n\n' + \
                   res['msg'] + '\n\nA complete dump of the error:\n\n' + str(res)
        mail(sender=sender, subject=subject, body=body)

    def v2_runner_on_async_failed(self, result):

        host = result._host.get_name()
        res = result._result

        sender = '"Ansible: %s" <root>' % host
        if isinstance(res, basestring):
            subject = 'Async failure: %s' % res.strip('\r\n').split('\n')[-1]
            body = 'An error occurred for host ' + host + ' with the following message:\n\n' + res
        else:
            subject = 'Async failure: %s' % res['msg'].strip('\r\n').split('\n')[0]
            body = 'An error occurred for host ' + host + ' with the following message:\n\n' + \
                   res['msg'] + '\n\nA complete dump of the error:\n\n' + str(res)
        mail(sender=sender, subject=subject, body=body)
