Protoplaster
============
An automated framework for platform testing (Hardware and BSPs).

Currently includes tests for:
{% for test_doc in tests_doc_list %}
* {{ test_doc.test_class_name  }}
{% for macro in test_doc.test_macros -%}
{% import macro.test_macro_file as jinja2_macros -%}
{% for devices_spec in test_doc.test_details -%}
{% for device_spec in devices_spec %}
  {%- if jinja2_macros[macro.test_macro_name](device_spec) %}
    * {{ jinja2_macros[macro.test_macro_name](device_spec) }}
  {%- endif %}
{%- endfor %}
{%- endfor %}
{%- endfor %}
{% endfor %}
