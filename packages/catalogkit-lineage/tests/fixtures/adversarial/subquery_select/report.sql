select (select max(id) from orders) as max_id, customer_id from orders
