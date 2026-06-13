{#
  type_string() / type_float()
  Return the correct type name for a CAST, per warehouse.

  Why this exists:
    DuckDB   -> varchar / double
    BigQuery -> string  / float64

  Usage: cast(commission_id as {{ type_string() }})
         cast(amount      as {{ type_float() }})
#}
{% macro type_string() %}
    {%- if target.type == 'bigquery' -%}string{%- else -%}varchar{%- endif -%}
{% endmacro %}

{% macro type_float() %}
    {%- if target.type == 'bigquery' -%}float64{%- else -%}double{%- endif -%}
{% endmacro %}
