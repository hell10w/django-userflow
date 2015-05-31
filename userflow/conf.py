# encoding: utf-8

import sys
import importlib

from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.http.response import HttpResponse


__all__ = ()


class setting(object):
    def __init__(self, name, default, auto_import=False):
        self.name = name
        self.default = default
        self.auto_import = auto_import

    def value(self):
        result = getattr(django_settings, self.name, self.default)
        if self.default:
            if type(result) != type(self.default):
                raise ImproperlyConfigured()
        if self.auto_import:
            if isinstance(result, (list, tuple)):
                result = map(import_attr, result)
            else:
                result = import_attr(result)
        return result


class settings(dict):
    def __init__(self, *args, **kwargs):
        iterable = (self._check_value(item)
                    for item in args)
        super(settings, self).__init__(iterable, **kwargs)

    def _check_value(self, item):
        assert isinstance(item, setting)
        return item.name, item.value()

    def update(self, other=None, **kwargs):
        raise RuntimeError


def import_attr(attr):
    module_name, attr = attr.rsplit('.', 1)
    module = importlib.import_module(module_name)
    return getattr(module, attr, None)


SETTINGS = settings(
    setting('USERS_FLOW_UP',
            ('userflow.pipeline.auth.signin',
             'userflow.pipeline.auth.signup',
             'userflow.pipeline.redirects.next_redirect',
             'userflow.pipeline.redirects.login_redirect', ),
            auto_import=True),
    setting('USERS_FLOW_DOWN',
            ('userflow.pipeline.auth.signout',
             'userflow.pipeline.redirects.next_redirect',
             'userflow.pipeline.redirects.index_redirect', ),
            auto_import=True),

    setting('USERS_SIGNUP_FORM',
            'userflow.forms.signup.SignupForm',
            auto_import=True),
    setting('USERS_SIGNIN_FORM',
            'userflow.forms.signin.SigninForm',
            auto_import=True),

)


class Wrapper(object):
    def __init__(self, wrapped):
        super(Wrapper, self).__init__()
        self.wrapped = wrapped

    @property
    def is_default_user_model(self):
        return getattr(django_settings, 'AUTH_USER_MODEL') == 'auth.User'

    @property
    def is_generic_user_model(self):
        return getattr(django_settings, 'AUTH_USER_MODEL') == 'userflow.User'

    def run_flow(self, flow, *args, **kwargs):
        flow_actions = getattr(self, flow)
        for action in flow_actions:
            response = action(*args, **kwargs)
            if isinstance(response, HttpResponse):
                return response
        raise ImproperlyConfigured()

    def __getattribute__(self, name):
        try:
            return super(Wrapper, self).__getattribute__(name)
        except AttributeError:
            return self.wrapped.SETTINGS[name]

sys.modules[__name__] = Wrapper(sys.modules[__name__])