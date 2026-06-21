with first_pass as (
    select id as order_id, amount as gross_amount from a
), second_pass as (
    select order_id, gross_amount as net_amount from first_pass
)
select order_id, net_amount from second_pass
