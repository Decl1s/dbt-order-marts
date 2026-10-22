-- Сначала проверяем строковое представление, чтобы CAST не округлял дробные копейки.
select * from {{ ref('raw_orders') }}
where not regexp_full_match(amount_cents, '[1-9][0-9]{0,6}')
