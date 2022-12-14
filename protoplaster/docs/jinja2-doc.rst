Hardware testing
================
In order to test Hardware/BSP an open-source framework ``Protoplaster`` has been created. There are required a yaml file as an input to decide which tests should be run and pass the data necessary to performence tests, for example address and bus number when you want to test the i2c interface. The example of such a file and detailed usage description is avaiable in the `Github repository <https://github.com/antmicro/protoplaster>`_.

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
