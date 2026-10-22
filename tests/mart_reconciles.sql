-- Независимо сверяем итог витрины с фактом, а не с другой копией того же JOIN.
with expected as (
    select count(*) as orders, coalesce(sum(gross_cents), 0) as gross,
        coalesce(sum(refunded_cents), 0) as refunded, coalesce(sum(net_cents), 0) as net
    from {{ ref('fct_orders') }} where status = 'paid'
), actual as (
    select coalesce(sum(paid_orders), 0) as orders, coalesce(sum(gross_cents), 0) as gross,
        coalesce(sum(refunded_cents), 0) as refunded, coalesce(sum(net_cents), 0) as net
    from {{ ref('mart_daily_channel') }}
)
select * from expected e cross join actual a
where e.orders <> a.orders or e.gross <> a.gross or e.refunded <> a.refunded or e.net <> a.net
