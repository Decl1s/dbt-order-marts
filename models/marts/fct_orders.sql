-- Зерно факта — один заказ, включая отменённые. Денежные суммы целые копейки.
with joined as (
    select o.*,
        coalesce(r.refunded_cents, 0)::bigint as refunded_cents
    from {{ ref('stg_orders') }} as o
    left join {{ ref('int_refunds_by_order') }} as r using (order_id)
)
select order_id, order_date, channel, status,
    case when status = 'paid' then amount_cents else 0 end::bigint as gross_cents,
    refunded_cents,
    (case when status = 'paid' then amount_cents else 0 end - refunded_cents)::bigint as net_cents
from joined
