select customer_id, amount, sum(amount) over (partition by customer_id) as customer_total from orders
