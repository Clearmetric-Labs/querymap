select
    sum(case when raw_payments.payment_method = 'credit_card' then raw_payments.amount else 0 end) as credit_card_amount
from raw_payments
