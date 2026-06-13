{#
  to_year_month(date_expr)
  Format a date as 'YYYY-MM' (e.g. '2026-05'), cross-dialect.

  Why this exists:
    DuckDB   -> strftime(date_expr, '%Y-%m')      (value first)
    BigQuery -> format_date('%Y-%m', date_expr)   (format string first)
#}
{% macro to_year_month(date_expr) %}
    {%- if target.type == 'bigquery' -%}
        format_date('%Y-%m', {{ date_expr }})
    {%- else -%}
        strftime({{ date_expr }}, '%Y-%m')
    {%- endif -%}
{% endmacro %}
