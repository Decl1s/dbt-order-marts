-- Одна строка — один заказ; неверный тип даты даёт отказ, а не тихий NULL.
select
    order_id,
    cast(order_date as date) as order_date,
    channel,
    status,
    cast(amount_cents as bigint) as amount_cents
from {{ ref('raw_orders') }}
