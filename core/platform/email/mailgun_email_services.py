# coding: utf-8
#
# Copyright 2016 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Provides mailgun api to send emails."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import base64

import feconf
import python_utils

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_to_recipients(
        sender_email, recipient_emails, subject,
        plaintext_body, html_body, bcc=None, reply_to=None,
        recipient_variables=None):
    try:
        if not feconf.SMTP_SERVER_HOST:
            raise Exception('SMTP server host is not available.')

        if not feconf.SMTP_SERVER_LOGIN:
            raise Exception('SMTP server login is not available.')

        if not feconf.SMTP_SERVER_PASSWORD:
            raise Exception('SMTP server password is not available.')

        for recipient_email in recipient_emails:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender_email
            message["To"] = recipient_email

            part1 = MIMEText(plaintext_body, "plain")
            part2 = MIMEText(html_body, "html")

            message.attach(part1)
            message.attach(part2)

            server = smtplib.SMTP_SSL(feconf.SMTP_SERVER_HOST, feconf.SMTP_SERVER_PORT)
            server.login(feconf.SMTP_SERVER_LOGIN.encode('utf-8'), feconf.SMTP_SERVER_PASSWORD.encode('utf-8'))
            server.sendmail(sender_email, recipient_email, message.as_string())
    except Exception as e:
            python_utils.PRINT("ERROR send_email_to_recipients: ", str(e))
            return False

    return True
