Provided tests
==============
{% for test_doc in tests_doc_list %}
* {{ test_doc.test_class_name  }}
{% for macro in test_doc.test_macros -%}
{% import macro.test_macro_file as jinja2_macros -%}
{% for devices_spec in test_doc.test_details -%}
{% for device_spec in devices_spec %}
  * {{ jinja2_macros[macro.test_macro_name](device_spec) }}
{% endfor %}
{%- endfor %}
{%- endfor %}
{% endfor %}
