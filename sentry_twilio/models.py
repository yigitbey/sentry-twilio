"""
sentry_twilio.models
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by Matt Robenolt.
:license: BSD, see LICENSE for more details.
"""

import re
import urllib
from django import forms
from django.utils.translation import ugettext_lazy as _
from sentry.plugins.bases.notify import NotificationPlugin
from twilio.rest import TwilioRestClient 

import sentry_twilio

phone_re = re.compile(r'^(\+[1-9][0-9]*(\([0-9]*\)|-[0-9]*-))?[0]?[1-9][0-9\- ]*$')  # +12-345-6789999 or 12-345-6789999
split_re = re.compile(r'\s*,\s*|\s+')

twilio_sms_endpoint = 'https://api.twilio.com/2010-04-01/Accounts/{0}/SMS/Messages.json'
twilio_call_endpoint = 'https://api.twilio.com/2010-04-01/Accounts/{0}/Calls.json'

class TwilioSMSConfigurationForm(forms.Form):
    account_sid = forms.CharField(label=_('Account SID'), required=True,
        widget=forms.TextInput(attrs={'class': 'span6'}))
    auth_token = forms.CharField(label=_('Auth Token'), required=True,
        widget=forms.PasswordInput(render_value=True, attrs={'class': 'span6'}))
    sms_from = forms.CharField(label=_('SMS From #'), required=True,
        help_text=_('Digits only'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 3305093095'}))
    sms_to = forms.CharField(label=_('SMS To #s'), required=True,
        help_text=_('Recipient(s) phone numbers separated by commas or lines'),
        widget=forms.Textarea(attrs={'placeholder': 'e.g. 33-050-9893095, +33-050-5555555555'}))

    def clean_sms_from(self):
        data = self.cleaned_data['sms_from']
        if not phone_re.match(data):
            raise forms.ValidationError('{0} is not a valid phone number.'.format(data))
        if not data.startswith('+1'):
            # Append the +1 when saving
            data = '+1' + data
        return data

    def clean_sms_to(self):
        data = self.cleaned_data['sms_to']
        phones = set(filter(bool, split_re.split(data)))
        for phone in phones:
           if not phone_re.match(phone):
               raise forms.ValidationError('{0} is not a valid phone number.'.format(phone))

        return ','.join(phones)
        
    def clean(self):
        # TODO: Ping Twilio and check credentials (?)
        return self.cleaned_data


class TwilioCallConfigurationForm(forms.Form):
    account_sid = forms.CharField(label=_('Account SID'), required=True,
        widget=forms.TextInput(attrs={'class': 'span6'}))
    auth_token = forms.CharField(label=_('Auth Token'), required=True,
        widget=forms.PasswordInput(render_value=True, attrs={'class': 'span6'}))
    call_from = forms.CharField(label=_('Call From #'), required=True,
        help_text=_('Digits only'),
        widget=forms.TextInput(attrs={'placeholder': 'e.g. 3305093095'}))
    call_to = forms.CharField(label=_('Call To #s'), required=True,
        help_text=_('Recipient(s) phone numbers separated by commas or lines'),
        widget=forms.Textarea(attrs={'placeholder': 'e.g. 33-050-9893095, +33-050-5555555555'}))
    twiml_url = forms.CharField(label=_('Twiml response URL.'), required=True,
        help_text=_('Twiml response URL.  Message parameter will be appended to this url.'),
        widget=forms.Textarea(attrs={'placeholder': 'http://twimlets.com/message?'}))
    
    
    def clean_call_from(self):
        data = self.cleaned_data['call_from']
        if not phone_re.match(data):
            raise forms.ValidationError('{0} is not a valid phone number.'.format(data))
        if not data.startswith('+1'):
            # Append the +1 when saving
            data = '+1' + data
        return data

    def clean_twiml_url(self):
        # TODO: check URL
        return self.cleaned_data['twiml_url']
        
        
    def clean_call_to(self):
        data = self.cleaned_data['call_to']
        phones = set(filter(bool, split_re.split(data)))
        for phone in phones:
            if not phone_re.match(phone):
                raise forms.ValidationError('{0} is not a valid phone number.'.format(phone))

        return ','.join(phones)


        
    def clean(self):
        # TODO: Ping Twilio and check credentials (?)
        return self.cleaned_data

        
class TwilioSMSPlugin(NotificationPlugin):
    author = 'Matt Robenolt'
    author_url = 'https://github.com/mattrobenolt'
    version = sentry_twilio.VERSION
    description = 'A plugin for Sentry which sends SMS notifications via Twilio'
    resource_links = (
        ('Documentation', 'https://github.com/mattrobenolt/sentry-twilio/blob/master/README.md'),
        ('Bug Tracker', 'https://github.com/mattrobenolt/sentry-twilio/issues'),
        ('Source', 'https://github.com/mattrobenolt/sentry-twilio'),
        ('Twilio', 'http://www.twilio.com/'),
    )

    slug = 'twilio_sms'
    title = _('Twilio (SMS)')
    conf_title = title
    conf_key = 'twilio_sms'
    project_conf_form = TwilioSMSConfigurationForm

    
    def is_configured(self, request, project, **kwargs):
        return all([self.get_option(o, project) for o in ('account_sid', 'auth_token', 'sms_from', 'sms_to')])

    def get_send_to(self, *args, **kwargs):
        # This doesn't depend on email permission... stuff.
        return True

    def notify_users(self, group, event):
        project = group.project

        body = 'Sentry [{0}] {1}: {2}'.format(
            project.name.encode('utf-8'),
            event.get_level_display().upper().encode('utf-8'),
            event.error().encode('utf-8').splitlines()[0]
        )
        body = body[:160]  # Truncate to 160 characters

        account_sid = self.get_option('account_sid', project)
        auth_token = self.get_option('auth_token', project)
        sms_from = self.get_option('sms_from', project)
        sms_to = self.get_option('sms_to', project).split(',')

        client = TwilioRestClient(account_sid, auth_token)

        for phone in sms_to:
            client.sms.messages.create(to=phone, from_=sms_from, body=body)

        

                
class TwilioCallPlugin(NotificationPlugin):
    author = 'Matt Robenolt'
    author_url = 'https://github.com/mattrobenolt'
    version = sentry_twilio.VERSION
    description = 'A plugin for Sentry which calls phones via Twilio'
    resource_links = (
        ('Documentation', 'https://github.com/mattrobenolt/sentry-twilio/blob/master/README.md'),
        ('Bug Tracker', 'https://github.com/mattrobenolt/sentry-twilio/issues'),
        ('Source', 'https://github.com/mattrobenolt/sentry-twilio'),
        ('Twilio', 'http://www.twilio.com/'),
    )

    slug = 'twilio_call'
    title = _('Twilio (Call)')
    conf_title = title
    conf_key = 'twilio_call'
    project_conf_form = TwilioCallConfigurationForm

    def is_configured(self, request, project, **kwargs):
        return all([self.get_option(o, project) for o in ('account_sid', 'auth_token', 'call_from', 'call_to','twiml_url')])

    def get_send_to(self, *args, **kwargs):
        # This doesn't depend on email permission... stuff.
        return True

    def notify_users(self, group, event):
        project = group.project

        message_body = 'Sentry {1}: {2}'.format(
            project.name.encode('utf-8'),
            event.get_level_display().upper().encode('utf-8'),
            event.error().encode('utf-8').splitlines()[0]
        )
        body = { 'message': message_body }
        
        message_body = urllib.urlencode(body)
        
        account_sid = self.get_option('account_sid', project)
        auth_token = self.get_option('auth_token', project)
        call_from = self.get_option('call_from', project)
        call_to = self.get_option('call_to', project).split(',')
        twiml_url = self.get_option('twiml_url', project) + "&" + message_body
                                
        client = TwilioRestClient(account_sid, auth_token)

        for phone in call_to:
            client.calls.create(to=phone,
                                   from_=call_from,
                                   url=twiml_url)

        
