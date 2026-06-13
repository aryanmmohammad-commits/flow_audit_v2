{#
  date_offset(date_expr, n, unit, direction='sub')
  Add or subtract an interval from a date, cross-dialect.

  Why this exists:
    DuckDB   -> date_expr - interval 90 day        (operator + bare interval)
    BigQuery -> DATE_SUB(date_expr, INTERVAL 90 DAY) (function form)

  direction = 'sub' (default) or 'add'.
  Example: {{ date_offset("date '" ~ var('as_of_date') ~ "'", 90, 'day') }}
#}
{% macro date_offset(date_expr, n, unit, direction='sub') %}
    {%- if target.type == 'bigquery' -%}
        {%- if direction == 'add' -%}
            date_add({{ date_expr }}, interval {{ n }} {{ unit | upper }})
        {%- else -%}
            date_sub({{ date_expr }}, interval {{ n }} {{ unit | upper }})
        {%- endif -%}
    {%- else -%}
        {%- if direction == 'add' -%}
            cast({{ date_expr }} + interval {{ n }} {{ unit }} as date)
        {%- else -%}
            cast({{ date_expr }} - interval {{ n }} {{ unit }} as date)
        {%- endif -%}
    {%- endif -%}
{% endmacro %}
