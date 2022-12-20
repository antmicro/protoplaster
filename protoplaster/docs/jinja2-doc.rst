Hardware testing
================
In order to test Hardware/BSP an open-source framework ``Protoplaster`` has been created. There are required a yaml file as an input to decide which tests should be run and pass the data necessary to performence tests, for example address and bus number when you want to test the i2c interface. The example of such a file and detailed usage description is avaiable in the `Github repository <https://github.com/antmicro/protoplaster>`_.

{% for module_doc in tests_doc_list -%}
 {% set prefix = [] -%}
 {% for class in module_doc.class_macros -%}
  {% import class.test_macro_file as jinja2_class_macros with context -%}
  {% if jinja2_class_macros[class.test_macro_name](prefix) -%}
   {{ jinja2_class_macros[class.test_macro_name](prefix) }}
  {% endif -%}
 {% endfor -%}
 {% for devices_spec in module_doc.test_details -%}
  {% for dev_type in devices_spec -%}
   {% set val_list = [] -%}
   {% for dev_spec in dev_type.items() -%}
    {% do val_list.append(dev_spec[1]) -%}
   {%- endfor -%}
   {% if prefix[0]|length %}
    * {{ prefix[0] }}{{ val_list[0] }}:
   {% else %}
    * {{ val_list[0] }}:
   {% endif -%}
   {%- for macro in module_doc.test_macros -%}
    {% import macro.test_macro_file as jinja2_macros -%}
    {% if jinja2_macros[macro.test_macro_name](dev_type) %}
     * {{ jinja2_macros[macro.test_macro_name](dev_type) }}
    {% endif -%}
   {% endfor %}
  {% endfor %}
 {% endfor %}
{% endfor -%}
