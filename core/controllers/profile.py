# Copyright 2014 The Oppia Authors. All Rights Reserved.
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

"""Controllers for the profile page."""

from __future__ import absolute_import  # pylint: disable=import-only-modules
from __future__ import unicode_literals  # pylint: disable=import-only-modules

import base64
import json
import re
import zipfile

from constants import constants
from core.controllers import acl_decorators
from core.controllers import base
from core.domain import email_manager
from core.domain import role_services
from core.domain import subscription_services
from core.domain import summary_services
from core.domain import takeout_service
from core.domain import user_services
from core.domain import wipeout_service
from core.platform import models
from core.platform.email.mailgun_email_services import send_email_to_recipients
import feconf
import python_utils
import utils
import uuid

current_user_services = models.Registry.import_current_user_services()


class ProfilePage(base.BaseHandler):
    """The world-viewable profile page."""

    @acl_decorators.open_access
    def get(self, username):
        """Handles GET requests for the publicly-viewable profile page."""

        user_settings = user_services.get_user_settings_from_username(username)

        if not user_settings:
            raise self.PageNotFoundException

        self.render_template('profile-page.mainpage.html')


class ProfileHandler(base.BaseHandler):
    """Provides data for the profile page."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.open_access
    def get(self, username):
        """Handles GET requests."""

        user_settings = user_services.get_user_settings_from_username(username)
        if not user_settings:
            raise self.PageNotFoundException

        created_exp_summary_dicts = []
        edited_exp_summary_dicts = []

        subscriber_ids = subscription_services.get_all_subscribers_of_creator(
            user_settings.user_id)
        is_already_subscribed = (self.user_id in subscriber_ids)
        is_user_visiting_own_profile = (self.user_id == user_settings.user_id)

        user_contributions = user_services.get_user_contributions(
            user_settings.user_id)
        if user_contributions:
            created_exp_summary_dicts = (
                summary_services.get_displayable_exp_summary_dicts_matching_ids(
                    user_contributions.created_exploration_ids))
            edited_exp_summary_dicts = (
                summary_services.get_displayable_exp_summary_dicts_matching_ids(
                    user_contributions.edited_exploration_ids))
        profile_is_of_current_user = (self.username == username)

        self.values.update({
            'profile_is_of_current_user': profile_is_of_current_user,
            'username_of_viewed_profile': user_settings.username,
            'user_bio': user_settings.user_bio,
            'subject_interests': user_settings.subject_interests,
            'first_contribution_msec': (
                user_settings.first_contribution_msec
                if user_settings.first_contribution_msec else None),
            'profile_picture_data_url': user_settings.profile_picture_data_url,
            'user_impact_score': user_services.get_user_impact_score(
                user_settings.user_id),
            'created_exp_summary_dicts': created_exp_summary_dicts,
            'edited_exp_summary_dicts': edited_exp_summary_dicts,
            'is_already_subscribed': is_already_subscribed,
            'is_user_visiting_own_profile': is_user_visiting_own_profile
        })
        self.render_json(self.values)


class PreferencesPage(base.BaseHandler):
    """The preferences page."""

    @acl_decorators.can_manage_own_account
    def get(self):
        """Handles GET requests."""
        self.render_template('preferences-page.mainpage.html')


class PreferencesHandler(base.BaseHandler):
    """Provides data for the preferences page."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.can_manage_own_account
    def get(self):
        """Handles GET requests."""
        user_settings = user_services.get_user_settings(self.user_id)
        user_email_preferences = user_services.get_email_preferences(
            self.user_id)

        creators_subscribed_to = subscription_services.get_all_creators_subscribed_to( # pylint: disable=line-too-long
            self.user_id)
        creators_settings = user_services.get_users_settings(
            creators_subscribed_to)
        subscription_list = []

        for index, creator_settings in enumerate(creators_settings):
            subscription_summary = {
                'creator_picture_data_url': (
                    creator_settings.profile_picture_data_url),
                'creator_username': creator_settings.username,
                'creator_impact': (
                    user_services.get_user_impact_score(
                        creators_subscribed_to[index]))
            }

            subscription_list.append(subscription_summary)

        self.values.update({
            'preferred_language_codes': user_settings.preferred_language_codes,
            'preferred_site_language_code': (
                user_settings.preferred_site_language_code),
            'preferred_audio_language_code': (
                user_settings.preferred_audio_language_code),
            'profile_picture_data_url': user_settings.profile_picture_data_url,
            'default_dashboard': user_settings.default_dashboard,
            'user_bio': user_settings.user_bio,
            'subject_interests': user_settings.subject_interests,
            'can_receive_email_updates': (
                user_email_preferences.can_receive_email_updates),
            'can_receive_editor_role_email': (
                user_email_preferences.can_receive_editor_role_email),
            'can_receive_feedback_message_email': (
                user_email_preferences.can_receive_feedback_message_email),
            'can_receive_subscription_email': (
                user_email_preferences.can_receive_subscription_email),
            'subscription_list': subscription_list,
            'name': user_settings.name,
            'surname': user_settings.surname
        })
        self.render_json(self.values)

    @acl_decorators.can_manage_own_account
    def put(self):
        """Handles PUT requests."""
        update_type = self.payload.get('update_type')
        data = self.payload.get('data')

        if update_type == 'user_bio':
            if len(data) > feconf.MAX_BIO_LENGTH_IN_CHARS:
                raise self.InvalidInputException(
                    'User bio exceeds maximum character limit: %s'
                    % feconf.MAX_BIO_LENGTH_IN_CHARS)
            else:
                user_services.update_user_bio(self.user_id, data)
        elif update_type == 'password':
            user_services.set_user_info(user_id=self.user_id, password=python_utils.hash_password(data))
        elif update_type == 'name':
            user_services.set_user_info(user_id=self.user_id, name=data)
        elif update_type == 'surname':
            user_services.set_user_info(user_id=self.user_id, surname=data)
        elif update_type == 'subject_interests':
            user_services.update_subject_interests(self.user_id, data)
        elif update_type == 'preferred_language_codes':
            user_services.update_preferred_language_codes(self.user_id, data)
        elif update_type == 'preferred_site_language_code':
            user_services.update_preferred_site_language_code(
                self.user_id, data)
        elif update_type == 'preferred_audio_language_code':
            user_services.update_preferred_audio_language_code(
                self.user_id, data)
        elif update_type == 'profile_picture_data_url':
            user_services.update_profile_picture_data_url(self.user_id, data)
        elif update_type == 'default_dashboard':
            user_services.update_user_default_dashboard(self.user_id, data)
        elif update_type == 'email_preferences':
            user_services.update_email_preferences(
                self.user_id, data['can_receive_email_updates'],
                data['can_receive_editor_role_email'],
                data['can_receive_feedback_message_email'],
                data['can_receive_subscription_email'])
        else:
            raise self.InvalidInputException(
                'Invalid update type: %s' % update_type)

        self.render_json({})


class ProfilePictureHandler(base.BaseHandler):
    """Provides the dataURI of the user's profile picture, or none if no user
    picture is uploaded.
    """

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.can_manage_own_account
    def get(self):
        """Handles GET requests."""
        user_settings = user_services.get_user_settings(self.user_id)
        self.values.update({
            'profile_picture_data_url': user_settings.profile_picture_data_url
        })
        self.render_json(self.values)


class ProfilePictureHandlerByUsernameHandler(base.BaseHandler):
    """Provides the dataURI of the profile picture of the specified user,
    or None if no user picture is uploaded for the user with that ID.
    """

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.open_access
    def get(self, username):
        user_id = user_services.get_user_id_from_username(username)
        if user_id is None:
            raise self.PageNotFoundException

        user_settings = user_services.get_user_settings(user_id)
        self.values.update({
            'profile_picture_data_url_for_username': (
                user_settings.profile_picture_data_url)
        })
        self.render_json(self.values)


class SignupPage(base.BaseHandler):
    """The page which prompts for username and acceptance of terms."""

    REDIRECT_UNFINISHED_SIGNUPS = False

    @acl_decorators.require_user_id_else_redirect_to_homepage
    def get(self):
        """Handles GET requests."""
        return_url = self.request.get('return_url', self.request.uri)
        # Validating return_url for no external redirections.
        if re.match('^/[^//]', return_url) is None:
            return_url = '/'
        if user_services.has_fully_registered_account(self.user_id):
            self.redirect(return_url)
            return

        self.render_template('signup-page.mainpage.html')


class SignupHandler(base.BaseHandler):
    """Provides data for the editor prerequisites page."""

    REDIRECT_UNFINISHED_SIGNUPS = False

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.require_user_id_else_redirect_to_homepage
    def get(self):
        """Handles GET requests."""
        user_settings = user_services.get_user_settings(self.user_id)

        self.render_json({
            'can_send_emails': feconf.CAN_SEND_EMAILS,
            'has_agreed_to_latest_terms': bool(
                user_settings.last_agreed_to_terms and
                user_settings.last_agreed_to_terms >=
                feconf.REGISTRATION_PAGE_LAST_UPDATED_UTC),
            'has_ever_registered': bool(
                user_settings.username and user_settings.last_agreed_to_terms),
            'username': user_settings.username,
        })

    @acl_decorators.require_user_id_else_redirect_to_homepage
    def post(self):
        """Handles POST requests."""
        username = self.payload.get('username')
        agreed_to_terms = self.payload.get('agreed_to_terms')
        default_dashboard = self.payload.get('default_dashboard')
        can_receive_email_updates = self.payload.get(
            'can_receive_email_updates')

        has_ever_registered = user_services.has_ever_registered(self.user_id)
        has_fully_registered_account = (
            user_services.has_fully_registered_account(self.user_id))

        if has_fully_registered_account:
            self.render_json({})
            return

        if not isinstance(agreed_to_terms, bool) or not agreed_to_terms:
            raise self.InvalidInputException(
                'In order to edit explorations on this site, you will '
                'need to accept the license terms.')
        else:
            user_services.record_agreement_to_terms(self.user_id)

        if not user_services.get_username(self.user_id):
            try:
                user_services.set_user_info(user_id=self.user_id,
                                            new_username=username,
                                            role=self.payload.get('role'),
                                            password=python_utils.hash_password(self.payload.get('password')),
                                            email=self.payload.get('email'))

                user_settings = user_services.get_user_settings(self.user_id)
                token = uuid.uuid4().hex
                user_services.set_user_token(user_id=user_settings.user_id, token=token)
                link = feconf.OPPIA_SITE_URL + "/email_confirm?token=" + token

                send_email_to_recipients(sender_email=feconf.SENDER_EMAIL,
                                         recipient_emails=[user_settings.email],
                                         subject="Registration confirmation",
                                         plaintext_body=link,
                                         html_body=link)
            except utils.ValidationError as e:
                raise self.InvalidInputException(e)

        if can_receive_email_updates is not None:
            user_services.update_email_preferences(
                self.user_id, can_receive_email_updates,
                feconf.DEFAULT_EDITOR_ROLE_EMAIL_PREFERENCE,
                feconf.DEFAULT_FEEDBACK_MESSAGE_EMAIL_PREFERENCE,
                feconf.DEFAULT_SUBSCRIPTION_EMAIL_PREFERENCE)

        # Note that an email is only sent when the user registers for the first
        # time.
        if feconf.CAN_SEND_EMAILS and not has_ever_registered:
            email_manager.send_post_signup_email(self.user_id)

        user_services.generate_initial_profile_picture(self.user_id)

        if not has_ever_registered:
            # Set the default dashboard for new users.
            user_services.update_user_default_dashboard(
                self.user_id, default_dashboard)

        self.render_json({})


class DeleteAccountPage(base.BaseHandler):
    """The delete account page."""

    @acl_decorators.can_manage_own_account
    def get(self):
        """Handles GET requests."""
        if not constants.ENABLE_ACCOUNT_DELETION:
            raise self.PageNotFoundException
        self.render_template('delete-account-page.mainpage.html')


class DeleteAccountHandler(base.BaseHandler):
    """Provides data for the delete account page."""

    @acl_decorators.can_manage_own_account
    def delete(self):
        """Handles DELETE requests."""
        if not constants.ENABLE_ACCOUNT_DELETION:
            raise self.PageNotFoundException

        wipeout_service.pre_delete_user(self.user_id)
        self.render_json({'success': True})


class ExportAccountHandler(base.BaseHandler):
    """Provides user with relevant data for Takeout."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.can_manage_own_account
    def get(self):
        """Handles GET requests."""
        if not constants.ENABLE_ACCOUNT_EXPORT:
            raise self.PageNotFoundException

        # Retrieve user data.
        user_takeout_object = takeout_service.export_data_for_user(
            self.user_id)
        user_data = user_takeout_object.user_data
        user_images = user_takeout_object.user_images

        # Create zip file.
        temp_file = python_utils.string_io()
        with zipfile.ZipFile(
            temp_file, mode='w', compression=zipfile.ZIP_DEFLATED) as zfile:
            zfile.writestr('oppia_takeout_data.json', json.dumps(user_data))
            for image in user_images:
                b64_png_no_header = image.b64_image_data.split(',')[1]
                decoded_png = base64.b64decode(
                    python_utils.url_unquote_plus(b64_png_no_header))
                zfile.writestr('images/' + image.image_export_path, decoded_png)

        # Render file for download.
        self.render_downloadable_file(
            temp_file.getvalue(), 'oppia_takeout_data.zip', 'text/plain')


class PendingAccountDeletionPage(base.BaseHandler):
    """The account pending deletion page. This page is accessible by all users
    even if they are not scheduled for deletion. This is because users that are
    scheduled for deletion are logged out instantly when they try to login.
    """

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        if not constants.ENABLE_ACCOUNT_DELETION:
            raise self.PageNotFoundException
        self.render_template('pending-account-deletion-page.mainpage.html')


class UsernameCheckHandler(base.BaseHandler):
    """Checks whether a username has already been taken."""

    REDIRECT_UNFINISHED_SIGNUPS = False

    @acl_decorators.require_user_id_else_redirect_to_homepage
    def post(self):
        """Handles POST requests."""
        username = self.payload.get('username')
        try:
            user_services.UserSettings.require_valid_username(username)
        except utils.ValidationError as e:
            raise self.InvalidInputException(e)

        username_is_taken = user_services.is_username_taken(username)
        self.render_json({
            'username_is_taken': username_is_taken,
        })


class SiteLanguageHandler(base.BaseHandler):
    """Changes the preferred system language in the user's preferences."""

    @acl_decorators.can_manage_own_account
    def put(self):
        """Handles PUT requests."""
        site_language_code = self.payload.get('site_language_code')
        user_services.update_preferred_site_language_code(
            self.user_id, site_language_code)
        self.render_json({})


class UserInfoHandler(base.BaseHandler):
    """Provides info about user. If user is not logged in,
    return dict containing false as logged in status.
    """

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.open_access
    def get(self):
        """Handles GET requests."""
        # The following headers are added to prevent caching of this response.
        self.response.cache_control.no_store = True

        if self.username:
            user_actions = user_services.UserActionsInfo(self.user_id).actions
            user_settings = user_services.get_user_settings(
                self.user_id, strict=False)
            self.render_json({
                'is_moderator': (
                    user_services.is_at_least_moderator(self.user_id)),
                'is_admin': user_services.is_admin(self.user_id),
                'is_super_admin': (
                    current_user_services.is_current_user_super_admin()),
                'is_topic_manager': (
                    user_services.is_topic_manager(self.user_id)),
                'can_create_collections': bool(
                    role_services.ACTION_CREATE_COLLECTION in user_actions),
                'preferred_site_language_code': (
                    user_settings.preferred_site_language_code),
                'username': user_settings.username,
                'email': user_services.get_email_from_username(
                    user_settings.username),
                'user_is_logged_in': True
            })
        else:
            self.render_json({
                'user_is_logged_in': False
            })


class UrlHandler(base.BaseHandler):
    """The handler for generating login URL."""

    GET_HANDLER_ERROR_RETURN_TYPE = feconf.HANDLER_TYPE_JSON

    @acl_decorators.open_access
    def get(self):
        login_url = None
        if self.user_id:
            self.render_json({'login_url': None})
        else:
            if self.request and self.request.get('current_url'):
                target_url = self.request.get('current_url')
                login_url = (
                    current_user_services.create_login_url(target_url))
                self.render_json({'login_url': login_url})
            else:
                raise self.InvalidInputException(
                    'Incomplete or empty GET parameters passed'
                )


class PasswordRecoveryTokenHandler(base.BaseHandler):

    @acl_decorators.open_access
    def post(self):
        """Handles POST PasswordRecoveryTokenHandler requests."""

        email = self.payload.get('email')
        user_settings = user_services.get_user_settings_from_email(email)

        if not user_settings:
            return self.render_json({})

        token = uuid.uuid4().hex
        user_services.set_user_token(user_id=user_settings.user_id, token=token)

        link = feconf.OPPIA_SITE_URL + "/password_recovery?token=" + token
        send_email_to_recipients(sender_email=feconf.SENDER_EMAIL,
                                 recipient_emails=[user_settings.email],
                                 subject="Password recovery",
                                 plaintext_body=link,
                                 html_body=link)
        self.render_json({})


class PasswordRecoveryHandler(base.BaseHandler):

    @acl_decorators.open_access
    def post(self, token):
        """Handles POST PasswordRecoveryHandler requests."""

        # token = self.payload.get('token')
        password = python_utils.hash_password(self.payload.get('password'))

        if not token:
            raise Exception('Invalid token')

        user_settings = user_services.get_user_settings_from_token(token)

        if not user_settings:
            raise Exception('Invalid token')

        user_services.set_user_info(user_id=user_settings.user_id, password=password)
        user_services.remove_user_token(user_id=user_settings.user_id)
        self.render_json({})


class EmailConfirmTokenHandler(base.BaseHandler):

    @acl_decorators.open_access
    def post(self):
        """Handles POST EmailConfirmTokenHandler requests."""

        email = self.payload.get('email')
        user_settings = user_services.get_user_settings_from_email(email)

        if not user_settings:
            return self.render_json({})

        if user_settings.email_confirmed:
            raise Exception('Email aready confirmed')

        token = uuid.uuid4().hex
        user_services.set_user_token(user_id=user_settings.user_id, token=token)

        link = feconf.OPPIA_SITE_URL + "/email_confirm?token=" + token
        send_email_to_recipients(sender_email=feconf.SENDER_EMAIL,
                                 recipient_emails=[user_settings.email],
                                 subject="Registration confirmation",
                                 plaintext_body=link,
                                 html_body=link)
        self.render_json({})


class EmailConfirmHandler(base.BaseHandler):

    @acl_decorators.open_access
    def post(self, token):
        """Handles POST EmailConfirmHandler requests."""

        # token = self.payload.get('token')

        if not token:
            raise Exception('Invalid token')

        user_settings = user_services.get_user_settings_from_token(token)

        if not user_settings:
            raise Exception('Invalid token')

        user_services.user_email_confirm(user_id=user_settings.user_id)
        user_services.remove_user_token(user_id=user_settings.user_id)
        self.render_json({})
