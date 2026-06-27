select
    id as order_id,
    user_id as customer_id,
    amount
from raw_orders
