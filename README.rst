fforms: Functional HTML forms for Python
========================================

|Travis CI build status (Linux)| |Coverage Status|



``fforms`` is a Python HTML form validation library that allows you to
take control of the validation and rendering while minimizing
boilerplate and awkward constructions. ``fforms`` does not provide any
widgets or rendering assistance beyond ease of access to form values
and validation errors. It does, however, let you define and use custom
validators with extreme ease. Read on to see how!

Installation
------------

``fforms`` is a pure Python package with no dependencies, so
installing it should be very straightforward. I develop and test on
3.4, and have configured Jenkins to test 3.3. Soon I'll be adding 3.5
as well.

1. **Option A**: ``pip install fforms``
2. **Option B**: download the source code, change into the working
   directory, and run ``python setup.py install``

Features
--------

-  A familiar interface for use in views

.. code:: python

    form = fforms.bind_dotted(registration_form, request.POST, request.FILES)
    if request.method == 'POST':
        if form.is_valid():
            data = form.clean_data
            # do stuff with the data
            return redirect("/url/to/redirect")
    return render_template("template-name.html", form=form)

-  Logical data structures that allow easy access from templates

.. code:: html+jinja

    {% set field = form.username %}
    <input type="text"{#
        #} value="{{ field.raw_data|default("", True) }}"{#
        #} {% if field.error %}class="invalid"{% endif %}{#
        #} name="field.full_name">
    {% if field.error %}
        <span class="error-msg">{{ field.error }}</span>
    {% endif %}

    <ul>
        {% for field in form.attendees %}
            <input type="text" name="{{ field.full_name }}">
        {% endfor %}
    </ul>

- Easy to add custom validators

.. code:: python

    myform['product_id'].validator = validators.from_regex(
        "^[A-Z]{2}-[0-9]{3}-[0-9]{4}$"
        "Please provide a valid product ID in the format XX-NNN-NNNN")
    myform['state'].validator = validators.one_of(
        "ME", "NH", "VT",
        msg="We only serve the Northeast")
    def funky_validator(data):
        left, right = data[:4], data[4:]
        if (int(left, 16), right) not in VALUES:
            raise ValidationError("Invalid format", data)
        # more funky tests
        return process(left, right)  # Set the field value
    myform['funky-field'].validator = funky_validator

- Internationalization using your choice of framework.

.. code:: python

    def translate_msg(msg, kwargs):
        # msg is a str.format-formatted string, and kwargs has all the
        # field values.
        msg = _(msg)
        kwargs = {key: _(val) for key, val in kwargs.items()}
        return msg.format(**kwargs)

    fforms.validators.DeferredMessage.process_message = translate_msg

-  Pure Python with no outside dependencies. Don't bring in a gigantic
   web framework just to use their forms library


License
-------

This project is licensed under the MIT license.

Getting started
---------------

To use ``fforms``, you'll first need to define a schema for your
form. This is most easily accomplished by using
``fforms.schema.make_from_literal`` as follows

.. code:: python

    from fforms import make_from_literal, validators, bind_dotted
    schema = make_from_literal({
        'username': validators.from_regex("^[a-zA-Z][a-zA-Z0-9_]{0,25}"),
        'password': validators.chain(
            validators.limit_length(min=8, max=128),
            validators.from_regex("[a-z]",
                                  "{field.name} must contain lowercase letters"),
            validators.from_regex("[A-Z]",
                                  "{field.name} must contain uppercase letters"),
            validators.from_regex("[0-9]", "{field.name} must contain numbers"),
            validators.from_regex("[^a-zA-Z0-9]",
                                  "{field.name} must contain special characters")
        ),
        'password2': validators.ensure_str,
        'email': validators.email,
        'address': {
            'street': validators.chain(validators.ensure_str,
                                       validators.limit_length(min=2)),
            'street2': validators.ensure_str,
            'zip_code': validators.chain(validators.from_regex("^[0-9]+$"),
                                         validators.limit_length(min=5, max=5)),
            'state': validators.one_of("ME", "NH", "VT", "MA")
        },
        'tags': [
            {'name': validators.ensure_str}
        ],
    })
    schema.validator = validators.chain(
        schema.validator,  # The default is validators.all_children
        validators.key_matcher("password", "password2",
                               "Please ensure the two passwords match"))

    schema['tags'].validator = validators.chain(
          schema['tags'].validator,
          validators.limit_length(min=1, max=8)
    )

Once you have a schema object, you can bind it to data to create a
bound form object

.. code:: python

    form = bind_dotted(schema, {
        'username': 'felipeochoa',
        'password': '123abcDEF!@#',
        'password2': '123ABCdef!@#',
        'email': 'me@example',
        'address.street': '123 Main St.',
        'address.street2': 'Unit 1',
        'address.zip code': '1234',
        'tags:0.name': 'tag1',
        'tags:1.name': 'tag2',
    })
    assert not form.is_valid()
    for field in form:
        print("%s %r (%s)" % (field.name, field.clean_data, field.error))

Which will print out::

    username 'felipeochoa' (None)
    password '123abcDEF!@#' (None)
    password2 '123ABCdef!@#' (None)
    tags [{'name': 'tag1'}, {'name': 'tag2'}] (None)
    address None ()
    email 'me@example' (None)

(address does not have an error message of its own; all the errors are
in its children).

You can use this code in your views or templates in a conventient
fashion

.. code:: python

    def my_view(request):
        form = bind_dotted(registration_form, request.POST, request.FILES)
        if request.method == 'POST':
            if form.is_valid():
                data = form.clean_data
                # do stuff with the data
                return redirect("/url/to/redirect")
        return render_template("template", form=form)

.. code:: html+jinja

           {% if form.error %}
              <span class="error-msg">form.error</span>
           {% endif %}
           {# more stuff #}
           {% for field in form.tags %}
               <input type="text" value="{{ field.value }}" name="{{ field.full_name }}">
           {% endfor %}

Detailed Documentation
----------------------

``fforms`` operates on three basic concepts: Schema, Validators, and
Forms.


Schema
~~~~~~

Think of a schema like an unbound form. It contains the blueprint for
bound forms: field names, definitions, and validators. Schema form
trees that describe the form you are validating, so some schema can
have child schema that perform validation/conversion on a part of the
received data. Schema can be one of the following types

- **MapSchema** Like a Python dictionary, mapping names to
  sub-schema
- **SequenceSchema** A variable length list where all sub-schema are
  of the same kind.
- **LeafSchema** Does not contain any children of its own.

All three types of schema support their own validation, in addition to
any validation that their children might perform. E.g., if you have a
schema defined as

.. code:: python

      user_schema = {
          'username': limit_length(max=25),
          'password': ensure_complexity(numbers=True, uppercase=True),
          'password2': ensure_str,
      }

You can add a higher-level validator ``key_matcher('password',
'password2')`` that additionally verifies that the two values
match. You could then compose that schema into another one, e.g.

.. code:: python

    many_users_schema = [
        {
          'username': limit_length(max=25),
          'password': ensure_complexity(numbers=True, uppercase=True),
          'password2': ensure_str,
        }
    ]

This new schema would accept a list of ``username`` / ``password`` /
``password2`` combinations, which would be useful if you had to create
multiple users at the same time. You could then add a new validator
to, say, ensure no more than 5 users are created at a time
``limit_length(max=5)``.

Validators
~~~~~~~~~~

We've seen a few validators already, but haven't yet defined what they
are or what they do. Mechanically, validators are simply functions of
one value that produce another value. The argument is the value
attached to the field that the validator must check and/or
transform. For example, the ``as_int`` validator is defined as follows

.. code:: python

     def as_int(data):
         "Extract an integer from the data."
         try:
             return int(data)
         except (TypeError, ValueError):
             raise ValidationError("{field.name} must be a whole number", data)


Each schema can have two validators

- **Validator**: The validator stored under ``schema.validator`` will
  be called after the ``form.is_valid`` method is called and will take
  ``field.raw_data`` as its input. The output from this validator will
  be stored as ``field.clean_data``. If the validator raises
  ``ValidationError``, the message from the error will be extracted
  and set as ``field.error``, and ``field.clean_data`` will be left as
  ``None``. For schema with children, validators typically pass
  through the data unmodified, leaving all conversion to leaf
  nodes. In principle though, parent validators could modify the
  values generated by the child validators; **parent validators are
  run after child validators**. Though schema only have one validator,
  the nature of validators means that multiple validators can be easily
  composed into a bigger one.
- **Pre-processor**: The validator stored under
  ``schema.pre_processor`` will take the raw data provided to the
  field and transform it into a (still serialized) value. The return
  value of the validator will be saved as
  ``field.raw_data``. Pre-processing validators are called as soon as
  the field is bound, so should not do much validation work. In
  particular, the return value should still be "raw" (i.e.,
  serialized), since ``field.raw_data`` will be used directly in
  templates. Most applications should have no need to override the
  default pre-processor, which is a no-op. A notable exception is to
  provide a serialized value for any files passed in via
  ``request.FILES`` or similar.

Forms/Fields
~~~~~~~~~~~~

Forms (technically ``BoundField`` objects) marry the ``Schema`` with
data to be validated. Forms are typically created by calling
``Schema.bind`` or another helper function like
``bind_to_dotted``. Forms provide a nice API for accessing errors and
cleaned data. Like schema, forms are nodes in a tree structure (that
mirrors the schema they were built for).

Once you have a form object, calling its ``is_valid`` method will
return ``True`` if validation succeeded for the schema and ``False``
if it didn't. You will then be able to access the fields' ``.error``
and ``.clean_data`` arguments. The ``.error`` attribute stores a
string with the error message provided by the validator that rejected
the data. The ``.clean_data`` stores a de-serialized value that can
by passed to other parts of your application.



.. |Travis CI build status (Linux)| image:: https://travis-ci.org/felipeochoa/fforms.svg?branch=master
   :target: https://travis-ci.org/felipeochoa/fforms
.. |Coverage Status| image:: https://coveralls.io/repos/felipeochoa/fforms/badge.svg
   :target: https://coveralls.io/r/felipeochoa/fforms
