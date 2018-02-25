from paypalrestsdk import Payout, ResourceNotFound
from paypalrestsdk.exceptions import MissingConfig
import paypalrestsdk

def process_payout(batch):
    # TODO: delete this - for developing only
    paypalrestsdk.configure({
        "mode": "sandbox",  # sandbox or live
        "client_id": "AX3_V5iIbPLsEa_71d-pbfN2InBlMQPxTKqtwTMd1YxUxjxeIay75W6akP1ikLQ-4TpHMOoW7S-e5LOc",
        "client_secret": "EDuF-9rMsyA0PukAJ2BGNZingJ0GGsYoJ67hWTzRB9VtaBnaLRPLKSpYoIy25NjxEHZXZ7lYdZPh8v1B"})
    try:
        payout = Payout(batch.batch_body)
        print(payout)
        if payout.create():
            return {'status': 'Success',
                    'payout_batch_id': payout.batch_header.payout_batch_id}
        else:
            return {'status': 'Failed',
                    'error': payout.error}
    except Exception as e:
        return {'status': 'Failed',
                'error': e}
