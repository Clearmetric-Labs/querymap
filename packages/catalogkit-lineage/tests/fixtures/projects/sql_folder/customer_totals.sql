select
    customer_id,
    sum(amount) as total_amount
from orders_base
group by customer_id
