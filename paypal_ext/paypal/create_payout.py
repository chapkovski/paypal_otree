from paypalrestsdk import Payout, ResourceNotFound


def get_payout_body_of_batch(batch):
    header = batch.get_payout_header()
    items = batch.get_payout_items()
    payout = Payout({
        "sender_batch_header": header,
        "items": items,
    })

