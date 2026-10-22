-- Зерно витрины — дата заказа + канал. Возврат относится к дате заказа,
-- поэтому это экономика когорты заказов, а не кассовое движение по дате возврата.
select order_date, channel,
    count(*)::bigint as paid_orders,
    sum(gross_cents)::bigint as gross_cents,
    sum(refunded_cents)::bigint as refunded_cents,
    sum(net_cents)::bigint as net_cents
from {{ ref('fct_orders') }}
where status = 'paid'
group by order_date, channel
