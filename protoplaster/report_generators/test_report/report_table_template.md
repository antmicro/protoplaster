Protoplaster tests report
==================
|{% for field in fields %}{{field}}|{% endfor %}
|{% for field in fields %}---|{% endfor %}
{%- for row in reader %}
|{% for field in fields %}{% if field not in custom_columns %}{{row[field]}}{% else %}{{custom_columns[field](row[field])}}{% endif %}|{% endfor %}
{%- endfor %}