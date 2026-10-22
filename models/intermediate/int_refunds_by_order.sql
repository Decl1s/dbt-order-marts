-- Сначала меняем зерно: из события возврата в одну строку на order_id.
-- Без этого шага JOIN размножил бы сумму заказа при двух возвратах.
select order_id, sum(amount_cents)::bigint as refunded_cents
from {{ ref('stg_refunds') }}
group by order_id
