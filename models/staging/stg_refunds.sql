-- Возвраты — отдельные события. Один заказ может иметь несколько refund_id.
select refund_id, order_id, cast(amount_cents as bigint) as amount_cents
from {{ ref('raw_refunds') }}
