Hardware testing
================
In order to test Hardware/BSP an open-source framework ``Protoplaster`` has been created. There are required a yaml file as an input to decide which tests should be run and pass the data necessary to performence tests, for example address and bus number when you want to test the i2c interface. The example of such a file and detailed usage description is avaiable in the `Github repository <https://github.com/antmicro/protoplaster>`_.

{% for test_doc in tests_doc_list -%}
 {{ test_doc.test_class_name  }}
 {% for devices_spec in test_doc.test_details -%}
  {% for dev_type in devices_spec -%}
   {% set val_list = [] -%}
    {% for dev_spec in dev_type.items() -%}
     {{ val_list.append(dev_spec[1])|default("",True) }}
    {%- endfor %}
    * {{ val_list[0] }}:
    {%- for macro in test_doc.test_macros %}
     {% import macro.test_macro_file as jinja2_macros %}
     {%- if jinja2_macros[macro.test_macro_name](dev_type) %}
      * {{ jinja2_macros[macro.test_macro_name](dev_type) }}
    {% endif %}
   {%- endfor %}
  {% endfor %}
 {% endfor %}
{% endfor %}
