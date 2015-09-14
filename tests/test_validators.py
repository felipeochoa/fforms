# -*- coding: utf-8 -*-
"Unit testing of fforms.validators."

from decimal import Decimal
import unittest
from unittest import mock
from ast import literal_eval

import fforms.validators

from fforms import _patch_mock_callable
_patch_mock_callable()


class TestValidationError(unittest.TestCase):

    "Test the ValidationError class."

    def test_init(self):
        msg = mock.MagicMock()
        data = mock.MagicMock()
        err = fforms.validators.ValidationError(msg, data)
        self.assertIs(err.message, msg)
        self.assertIs(err.clean_data, data)
        self.assertEqual(err.args, (msg, data))

    def test_bind(self):
        msg = mock.MagicMock()
        data = mock.MagicMock()
        field = mock.MagicMock()
        err = fforms.validators.ValidationError(msg, data)
        bound = err.bind(field)
        msg.format.assert_called_once_with(field=field)
        self.assertEqual(bound, msg.format.return_value)


class TestDeferredMessage(unittest.TestCase):

    "Test the DeferredMessage class."

    def test_init(self):
        msg = mock.MagicMock()
        dmsg = fforms.validators.DeferredMessage(msg, a=1, b=2)
        self.assertIs(dmsg.msg, msg)
        self.assertEqual(dmsg.kwargs, {'a': 1, 'b': 2})

    def test_repr(self):
        msg = mock.MagicMock()
        dmsg = fforms.validators.DeferredMessage(msg)
        self.assertEqual(repr(dmsg), "DeferredMessage(%r, **{})" % msg)
        dmsg = fforms.validators.DeferredMessage(msg, a=1, b=2)
        rep = repr(dmsg)
        self.assertTrue(rep.startswith("DeferredMessage(%r, **{" % msg))
        self.assertTrue(rep.endswith("})"))
        dict_repr = rep[rep.find("{"):rep.find("}") + 1]
        self.assertEqual(literal_eval(dict_repr), dict(a=1, b=2))

    @mock.patch.object(fforms.validators.DeferredMessage, "process_message",
                       autospec=True)
    def test_format_calls_process_message(self, process_message):
        msg = mock.MagicMock()
        dmsg = fforms.validators.DeferredMessage(msg, a=1, b=2)
        ret = dmsg.format(c=3)
        process_message.assert_called_once_with(msg, dict(a=1, b=2, c=3))
        self.assertIs(ret, process_message.return_value)

    def test_format(self):
        msg = mock.MagicMock()
        dmsg = fforms.validators.DeferredMessage(msg, a=1, b=2)
        ret = dmsg.format(c=3)
        msg.format.assert_called_once_with(a=1, b=2, c=3)
        self.assertIs(ret, msg.format.return_value)

    def test_d_msg_no_user_msg_with_DM(self):
        msg = fforms.validators.DeferredMessage("abc", a=1)
        ret = fforms.validators.d_msg(None, msg, b=2)
        self.assertIsInstance(ret, fforms.validators.DeferredMessage)
        self.assertEqual(ret.msg, msg.msg)
        self.assertEqual(ret.kwargs, {'a': 1, 'b': 2})

    def test_d_msg_no_user_msg_not_DM(self):
        msg = "def"
        ret = fforms.validators.d_msg(None, msg, b=2)
        self.assertIsInstance(ret, fforms.validators.DeferredMessage)
        self.assertEqual(ret.msg, msg)
        self.assertEqual(ret.kwargs, {'b': 2})

    def test_d_msg_with_user_msg_with_DM(self):
        msg = fforms.validators.DeferredMessage("abc", a=1)
        ret = fforms.validators.d_msg(msg, "12345", b=2)
        self.assertIsInstance(ret, fforms.validators.DeferredMessage)
        self.assertEqual(ret.msg, msg.msg)
        self.assertEqual(ret.kwargs, {'a': 1, 'b': 2})

    def test_d_msg_with_user_msg_not_DM(self):
        msg = "abcdef"
        ret = fforms.validators.d_msg(msg, "12345", b=2)
        self.assertIsInstance(ret, fforms.validators.DeferredMessage)
        self.assertEqual(ret.msg, msg)
        self.assertEqual(ret.kwargs, {'b': 2})


class TestValidators(unittest.TestCase):

    "Test the various validator functions."

    def test_noop(self):
        x = mock.MagicMock()
        self.assertIs(fforms.validators.noop(x), x)

    def test_from_bool_func(self):
        val = fforms.validators.from_bool_func(lambda x: x % 2, "custom")
        self.assertEqual(val(9), 9)
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            val(8)
        self.assertIsInstance(cm.exception.message,
                              fforms.validators.DeferredMessage)
        self.assertEqual(cm.exception.message.msg, "custom")
        self.assertEqual(cm.exception.message.kwargs, {})
        self.assertEqual(cm.exception.clean_data, 8)
        # message is DeferredMessage
        msg = fforms.validators.DeferredMessage("123", a=1)
        val = fforms.validators.from_bool_func(lambda x: x % 2, msg)
        self.assertEqual(val(9), 9)
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            val(8)
        self.assertIs(cm.exception.message, msg)
        self.assertEqual(cm.exception.clean_data, 8)

    def test_chain(self):
        v1 = mock.MagicMock()
        v2 = mock.MagicMock()
        v3 = mock.MagicMock()
        x = mock.MagicMock()
        ret = fforms.validators.chain(v1, v2, v3)(x)
        v1.assert_called_once_with(x)
        v2.assert_called_once_with(v1.return_value)
        v3.assert_called_once_with(v2.return_value)
        self.assertIs(ret, v3.return_value)

    def test_chain_error(self):
        v1 = mock.MagicMock()
        v2 = mock.MagicMock(
            side_effect=fforms.validators.ValidationError("", None))
        v3 = mock.MagicMock()
        x = mock.MagicMock()
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.chain(v1, v2, v3), x,)
        v1.assert_called_once_with(x)
        v2.assert_called_once_with(v1.return_value)
        self.assertEqual(v3.call_count, 0)

    def test_limit_length_no_error(self):
        self.assertEqual("abc",
                         fforms.validators.limit_length()("abc"))
        self.assertEqual("123",
                         fforms.validators.limit_length(min=3)("123"))
        self.assertEqual("ABC",
                         fforms.validators.limit_length(max=3)("ABC"))
        self.assertEqual("jkl",
                         fforms.validators.limit_length(min=2, max=4)("jkl"))

    def test_limit_length_error_msg(self):
        err = fforms.validators.ValidationError
        self.assertRaises(err, fforms.validators.limit_length(min=3), "ab")
        self.assertRaises(err, fforms.validators.limit_length(max=3), "abcd")
        self.assertRaises(err, fforms.validators.limit_length(min=3, max=3),
                          "abcd")
        msg = "custom_message"
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.limit_length(min=3, msg=msg)("ab")
        self.assertEqual(cm.exception.message.msg, msg)
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.limit_length(max=3, msg=msg)("abcd")
        self.assertEqual(cm.exception.message.msg, msg)
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.limit_length(min=2, max=3, msg=msg)("abcd")
        self.assertEqual(cm.exception.message.msg, msg)

    def test_not_none(self):
        x = 12345
        self.assertIs(fforms.validators.not_none(x), x)
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.not_none, None)

    def test_key_matcher(self):
        d = {'key1': 123, 'key2': 123}
        val = fforms.validators.key_matcher('key1', 'key2')
        self.assertIs(val(d), d)
        self.assertRaises(fforms.validators.ValidationError,
                          val, {'key1': 123, 'key2': 456})
        msg = "custom_message"
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.key_matcher('key1', 'key2', msg=msg)({
                'key1': 123, 'key2': 456})
        self.assertEqual(cm.exception.message.msg, msg)

    def test_one_of(self):
        x = 'abc'
        self.assertIs(x, fforms.validators.one_of('abc', 'def', 'jkl')(x))
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.one_of('abc', 'def', 'jkl'),
                          "lmnop")
        msg = "custom_message"
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.one_of('abc', 'def', msg=msg)('lmnop')
        self.assertEqual(cm.exception.message.msg, msg)

    def test_limit_chars(self):
        x = "]abc^"
        self.assertIs(x, fforms.validators.limit_chars("^a-zA-Z]")(x))
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.limit_chars("0-9"), x)
        msg = "custom_message"
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.limit_chars('!@#$%]', msg=msg)('abc')
        self.assertEqual(cm.exception.message.msg, msg)

    def test_ensure_parent(self):
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.ensure_parent, "abc")
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.ensure_parent, 123)
        exes = [(123, 456), [123, 456], {'a': 123, 'b': 456}, (), [], {}]
        for x in exes:
            self.assertIs(fforms.validators.ensure_parent(x), x)

    def test_fail_if_error(self):
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.fail_if_error(
                fforms.validators.ValidationError("child", 123))
        self.assertEqual(cm.exception.message, "")
        self.assertEqual(cm.exception.clean_data, None)
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.fail_if_error(
                fforms.validators.ValidationError("child", 123),
                "custom_msg", 1)
        self.assertEqual(cm.exception.message, "custom_msg")
        self.assertEqual(cm.exception.clean_data, 1)
        try:
            fforms.validators.fail_if_error(123, "custom_message", [123])
            fforms.validators.fail_if_error("abc")
            fforms.validators.fail_if_error([])
        except fforms.validators.ValidationError:
            self.fail("Raised ValidationError incorrectly")

    def test_all_children(self):
        exes = ([1, 2, 3],
                {'a': 123, 'b': 456})
        for x in exes:
            self.assertIs(fforms.validators.all_children(x), x)
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.all_children('abc')
        self.assertEqual(cm.exception.clean_data, "abc")
        data = ['abc', fforms.validators.ValidationError("", None)]
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            fforms.validators.all_children(data)
        self.assertEqual(cm.exception.message, "")
        self.assertEqual(cm.exception.clean_data, data)

    def test_as_int(self):
        self.assertEqual(fforms.validators.as_int("123"), 123)
        self.assertEqual(fforms.validators.as_int(123), 123)
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.as_int, "12.3")
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.as_int, [12])

    def test_as_date(self):
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.as_date("%Y-%m-%d"), 123)
        msg = "custom_message"
        val = fforms.validators.as_date("%Y-%m-%d", msg)
        data = "2014-10-15"
        ret = val(data)
        self.assertEqual((ret.year, ret.month, ret.day), (2014, 10, 15))
        for x in [123, "123", [1, 2, 3], {'a': 1}]:
            with self.assertRaises(fforms.validators.ValidationError) as cm:
                val(x)
            self.assertEqual(cm.exception.clean_data, x)
            self.assertEqual(cm.exception.message.msg, msg)

    def test_as_decimal(self):
        self.assertEqual(fforms.validators.as_decimal("12.3"),
                         Decimal("12.3"))
        self.assertEqual(fforms.validators.as_decimal("123"), 123)
        for x in ["abcd", [1, 2, 3], {'a': 1}]:
            with self.assertRaises(fforms.validators.ValidationError) as cm:
                fforms.validators.as_decimal(x)
            self.assertEqual(cm.exception.clean_data, x)

    def test_ensure_instance(self):
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.ensure_instance(float), 12)
        self.assertRaises(fforms.validators.ValidationError,
                          fforms.validators.ensure_instance((float, str)), 12)
        msg = "custom_message"
        val = fforms.validators.ensure_instance(int, msg)
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            val("11.5")
        self.assertEqual(cm.exception.clean_data, "11.5")
        self.assertEqual(val(12), 12)

    def test_ensure_str(self):
        cases = [
            ("123", True),
            ("", True),
            ("\u00ED", True),
            (123, False),
            (None, False),
            ([1, 2, 3], False),
            ({'a': 1}, False),
            ([], False),
            ({}, False),
        ]
        for data, is_valid in cases:
            if is_valid:
                self.assertEqual(data,
                                 fforms.validators.ensure_str(data))
            else:
                self.assertRaises(
                    fforms.validators.ValidationError,
                    fforms.validators.ensure_str, data)

    def test_from_regex(self):
        # error/not, msg/not
        val = fforms.validators.from_regex("[a-d]{3}-[0-6]")
        data = "abc-4"
        self.assertIs(val(data), data)
        self.assertRaises(fforms.validators.ValidationError,
                          val, "efg-9")
        msg = "custom_message"
        val = fforms.validators.from_regex("[a-d]{3}-[0-6]", msg)
        self.assertIs(val(data), data)
        with self.assertRaises(fforms.validators.ValidationError) as cm:
            val("efg-9")
        self.assertEqual(cm.exception.message.msg, msg)
        self.assertEqual(cm.exception.clean_data, "efg-9")

    def test_email(self):
        # Test cases taken from
        # blogs.msdn.com/b/testing123/archive/2009/02/05/email-address-test-cases.aspx
        cases = [
            ("email@domain.com", True),
            ("firstname.lastname@domain.com", True),
            ("email@subdomain.domain.com", True),
            ("firstname+lastname@domain.com", True),
            ("email@123.123.123.123", True),
            ("email@[123.123.123.123]", True),
            ('"email"@domain.com', True),
            ("1234567890@domain.com", True),
            ("email@domain-one.com", True),
            ("_______@domain.com", True),
            ("email@domain.name", True),
            ("email@domain.co.jp", True),
            ("firstname-lastname@domain.com", True),
            ("a@t.co", True),
            ("email@domain.web", True),
            ("user@xn--alliancefranaise-npb.nu", True),
            ######################################################
            ("plainaddress", False),
            ("#@%^%#$@#$@#.com", False),
            ("@domain.com", False),
            ("Joe Smith <email@domain.com>", False),
            ("email.domain.com", False),
            ("email@domain@domain.com", False),
            (".email@domain.com", False),
            ("email.@domain.com", False),
            ("email..email@domain.com", False),
            ("\u00C1\u00E9\u00CD@domain.com", False),
            ("email@domain.com (Joe Smith)", False),
            ("email@domain", False),
            ("email@-domain.com", False),
            ("email@domain..com", False),
            ('email@here.com', True),
            ('weirder-email@here.and.there.com', True),
            ('email@[127.0.0.1]', True),
            ('email@[2001:dB8::1]', True),
            ('email@[2001:dB8:0:0:0:0:0:1]', True),
            ('email@[::fffF:127.0.0.1]', True),
            ('example@valid-----hyphens.com', True),
            ('example@valid-with-hyphens.com', True),
            ('test@domain.with.idn.tld.उदाहरण.परीक्षा', True),
            ('email@localhost', False),
            ('"test@test"@example.com', True),
            ('example@atm.%s' % ('a' * 63), True),
            ('example@%s.atm' % ('a' * 63), True),
            ('example@%s.%s.atm' % ('a' * 63, 'b' * 10), True),
            ('example@atm.%s' % ('a' * 64), False),
            ('example@%s.atm.%s' % ('b' * 64, 'a' * 63), False),
            (None, False),
            ('', False),
            ('abc', False),
            ('abc@', False),
            ('abc@bar', False),
            ('a @x.cz', False),
            ('abc@.com', False),
            ('something@@somewhere.com', False),
            ('email@127.0.0.1', False),
            ('email@[127.0.0.256]', False),
            ('email@[2001:db8::12345]', False),
            ('email@[2001:db8:0:0:0:0:1]', False),
            ('email@[::ffff:127.0.0.256]', False),
            ('example@invalid-.com', False),
            ('example@-invalid.com', False),
            ('example@invalid.com-', False),
            ('example@inv-.alid-.com', False),
            ('example@inv-.-alid.com', False),
            ('test@example.com\n\n<script src="x.js">', False),
            # Quoted-string format (CR not allowed)
            ('"\\\011"@here.com', True),
            ('"\\\012"@here.com', False),
            ('trailingdot@shouldfail.com.', False),
            # Max length of domain name labels is 63 characters per RFC 1034.
            ('a@%s.us' % ('a' * 63), True),
            ('a@%s.us' % ('a' * 64), False),
            # Trailing newlines in username or domain not allowed
            ('a@b.com\n', False),
            ('a\n@b.com', False),
            ('"test@test"\n@example.com', False),
            ('a@[127.0.0.1]\n', False),
        ]
        custom_email = fforms.validators.EmailValidator("custom_message")
        for data, is_valid in cases:
            if is_valid:
                self.assertEqual(fforms.validators.email(data), data)
                self.assertEqual(custom_email(data), data)
            else:
                self.assertRaises(
                    fforms.validators.ValidationError,
                    fforms.validators.email, data)
                with self.assertRaises(fforms.validators.ValidationError) as cm:
                    custom_email(data)
                self.assertEqual(cm.exception.message, "custom_message")
