with layer_one as (
    select customer_id, amount from base
), layer_two as (
    select customer_id, amount as normalized_amount from layer_one
)
select customer_id, normalized_amount from layer_two
