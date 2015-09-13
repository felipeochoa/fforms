
import re


class ValidationError(Exception):

    """
    Raised by validators to indicate an error.
    """

    def __init__(self, message, clean_data):
        self.message = message
        self.clean_data = clean_data
        super().__init__(message)

    def bind(self, bound_field):
        "Fill in error messages with the bound field info. Returns self."
        return self.message.format(field=bound_field)


class DeferredMessage:

    """
    Message class with deferred formatting.

    Users of the library can substitute their own formatting procedure by
    overriding the class variable `process_message` with a function accepting
    two positional arguments: `msg` and `kwargs`. The default implementation
    simply returns `msg.format(**kwargs)`, but users can add translation or
    other modifications by replacing this function with their own.

    """

    process_message = staticmethod(lambda msg, kwargs: msg.format(**kwargs))

    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.kwargs = kwargs

    def format(self, **extra_kw):
        "Flatten the message into a string."
        extra_kw.update(self.kwargs)
        return self.process_message(self.msg, extra_kw)


def d_msg(user_msg, default, **kwargs):
    """
    Create a DeferredMessage with a default value for msg.

    The deferred message uses user_msg as its base, or default if user_msg is
    None. If user_msg (or default if user_msg is None) is a DeferredMessage,
    the new DeferredMessage uses the underlying base, and the keyword
    arguments are combined.

    """
    msg = user_msg if user_msg is not None else default
    if isinstance(msg, DeferredMessage):
        kwargs.update(msg.kwargs)
        msg = msg.msg
    return DeferredMessage(msg, **kwargs)


noop = lambda x: x


def from_bool_func(func, msg):
    """
    Converts a boolean-valued function into a validator.

    If the function returns True, data is passed through unchanged. If
    the function returns False, the validator raises a ValidationError with a
    single message, msg.

    """
    if not isinstance(msg, DeferredMessage):
        msg = DeferredMessage(msg)
    def bool_validator(data):
        if func(data):
            return data
        raise ValidationError(msg, data)
    return bool_validator


def chain(*validators):
    "Chain a series of validators, piping the results from one into another."
    def chained_validator(data):
        for val in validators:
            data = val(data)
        return data
    return chained_validator


def limit_length(min=0, max=None, msg=None):
    "Create a validator to ensure the length of data is between min and max."
    if max is None:
        msg = d_msg(msg, "The length of {field.name} must be at least {min}",
                    min=min)
        return from_bool_func(lambda data: min <= len(data), msg)
    msg = d_msg(msg,
                "The length of {field.name} must be between {min} and {max}",
                min=min, max=max)
    return from_bool_func(lambda data: min <= len(data) <= max, msg)


not_none = from_bool_func(lambda x: x is not None,
                          "{field.name} is required.")


def key_matcher(key1, key2, msg=None):
    "Ensures the values of two keys are equal."
    msg = d_msg(msg,
                "{field.name}[{key1}] does not equal {field.name}[{key2}]",
                key1=key1, key2=key2)
    return from_bool_func(lambda data: data[key1] == data[key2], msg)


def one_of(*values, msg=None):
    "Ensure data is one of the specified values."
    msg = d_msg(msg, "{field.name} must be one of {values}.",
                values=values)
    return from_bool_func(lambda data: data in values, msg)


def limit_chars(char_class, msg=None):
    "Ensure data only contains characters in the given class."
    pattern = "[^%s]" % char_class.replace("]", "\\]")
    regex = re.compile(pattern)
    def limit_chars_validator(data):
        if not regex.search(data):
            return data
        invalid = frozenset(regex.findall(data))
        inner_msg = d_msg(msg, "Invalid characters: {invalid_chars}",
                          invalid_chars=invalid, char_class=char_class)
        raise ValidationError(inner_msg, data)
    return chain(ensure_str, limit_chars_validator)


ensure_parent = from_bool_func(
    lambda data: isinstance(data, (dict, list, tuple)),
    "{field.name} must be a container")


def fail_if_error(child_value, msg="", data=None):
    "Check a child's value and raise ValidationError if it's an error."
    if isinstance(child_value, ValidationError):
        raise ValidationError(msg, data)

def all_children(data):
    "Ensures all the children are none-errors."
    ensure_parent(data)
    if isinstance(data, dict):
        children = data.values()
    elif isinstance(data, (list, tuple)):
        children = iter(data)
    for child in children:
        fail_if_error(child, "", data)
    return data


def as_int(data):
    "Extract an integer from the data"
    try:
        return int(data)
    except (TypeError, ValueError):
        raise ValidationError("{field.name} must be a whole number", data)


def as_date(format_, msg=None):
    "Try to parse a date from the given string."
    from datetime import datetime
    msg = d_msg(msg, "Date must be in {format_} format", format_=format_)
    def date_from_str_validator(data):
        try:
            return datetime.strptime(data, format_).date()
        except (TypeError, ValueError):
            raise ValidationError(msg, data)
        return data
    date_from_str_validator.__doc__ = \
      "Parse a %s-formatted string into a Date" % format_
    return date_from_str_validator


def as_decimal(data):
    "Extract a decimal from the data."
    import decimal
    try:
        return decimal.Decimal(data)
    except (TypeError, ValueError, decimal.InvalidOperation):
        raise ValidationError(DeferredMessage(
            "{field.name} must be a decimal number"), data)
    return data


def ensure_instance(class_sig, msg=None):
    "Ensure the data given is of the given class."
    msg = d_msg(msg, "{field.name} must be a {class_sig}",
                class_sig=class_sig)
    def ensure_instance_validator(data):
        if not isinstance(data, class_sig):
            raise ValidationError(msg, data)
        return data
    ensure_instance_validator.__doc__ = \
      "Ensure the data is an instance of %r" % (class_sig,)
    return ensure_instance_validator


ensure_str = ensure_instance(str)


def from_regex(pattern, msg=None):
    "Create a validator that ensures the data contains a given pattern."
    regex = re.compile(pattern)
    msg = d_msg(msg, '{field.name} does not match {pattern}', pattern=pattern)
    return chain(ensure_str, from_bool_func(regex.search, msg))


class EmailValidator(object):

    """
    Email Validator essentially taken from Django 1.8.4

    Copyright (c) Django Software Foundation and individual contributors.
    All rights reserved.

    Redistribution and use in source and binary forms, with or without modification,
    are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.

    2. Redistributions in binary form must reproduce the above copyright
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
    IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
    THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
    PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
    EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
    PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
    PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
    LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
    SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

    """

    message = DeferredMessage('Enter a valid email address.')
    user_regex = re.compile(
        r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\Z"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',  # quoted-string
        re.IGNORECASE)
    domain_regex = re.compile(
        # max length of the domain is 249: 254 (max email length) minus one
        # period, two characters for the TLD, @ sign, & one character before @.
        r'(?:[A-Z0-9](?:[A-Z0-9-]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z',
        re.IGNORECASE)
    literal_regex = re.compile(
        # literal form, ipv4 or ipv6 address (SMTP 4.1.3)
        r'\[([A-f0-9:\.]+)\]\Z',
        re.IGNORECASE)
    ip_v46_regex = re.compile(
        r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\Z')
    domain_whitelist = ['localhost']

    def __init__(self, message=None):
        if message is not None:
            self.message = message

    def __call__(self, value):
        ensure_str(value)

        if not value or '@' not in value:
            raise ValidationError(self.message, value)

        user_part, domain_part = value.rsplit('@', 1)

        if not self.user_regex.match(user_part):
            raise ValidationError(self.message, value)

        if (domain_part not in self.domain_whitelist and
                not self.validate_domain_part(domain_part)):
            # Try for possible IDN domain-part
            try:
                domain_part = domain_part.encode('idna').decode('ascii')
                if self.validate_domain_part(domain_part):
                    return
            except UnicodeError:
                pass
            raise ValidationError(self.message, value)
        return value

    def validate_domain_part(self, domain_part):
        if self.domain_regex.match(domain_part):
            return True

        literal_match = self.literal_regex.match(domain_part)
        if literal_match:
            ip_address = literal_match.group(1)
            if self.ip_v46_regex.match(ip_address):
                return True
        return False


email = EmailValidator()
