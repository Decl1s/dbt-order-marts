-- Проверяем агрегат до построения факта: возврат не превышает цену,
-- и отменённый заказ не может иметь возврат.
select r.order_id
from {{ ref('int_refunds_by_order') }} as r
join {{ ref('stg_orders') }} as o using (order_id)
where r.refunded_cents > o.amount_cents or o.status <> 'paid'
