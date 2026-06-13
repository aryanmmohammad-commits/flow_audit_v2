{#
  date_diff_unit(unit, start_date, end_date)
  Cross-dialect integer difference between two dates.

  Why this exists:
    DuckDB   -> date_diff('day', start, end)     unit first, as a STRING
    BigQuery -> DATE_DIFF(end, start, DAY)        dates first, unit as a KEYWORD,
                                                  and the date order is reversed.
  Call it the same way everywhere:  {{ date_diff_unit('day', 'a.entered_at', 'x') }}
#}
{% macro date_diff_unit(unit, start_date, end_date) %}
    {%- if target.type == 'bigquery' -%}
        date_diff({{ end_date }}, {{ start_date }}, {{ unit | upper }})
    {%- else -%}
        date_diff('{{ unit }}', {{ start_date }}, {{ end_date }})
    {%- endif -%}
{% endmacro %}
