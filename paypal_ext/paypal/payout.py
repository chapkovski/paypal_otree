from paypalrestsdk import Payout, ResourceNotFound
from paypalrestsdk.exceptions import MissingConfig
import paypalrestsdk

def create(batch):
    # TODO: delete this - for developing only
    paypalrestsdk.configure({
        "mode": "sandbox",  # sandbox or live
        "client_id": "AX3_V5iIbPLsEa_71d-pbfN2InBlMQPxTKqtwTMd1YxUxjxeIay75W6akP1ikLQ-4TpHMOoW7S-e5LOc",
        "client_secret": "EDuF-9rMsyA0PukAJ2BGNZingJ0GGsYoJ67hWTzRB9VtaBnaLRPLKSpYoIy25NjxEHZXZ7lYdZPh8v1B"})
    try:
        payout = Payout(batch.batch_body)
        if payout.create():
            batch.payout_batch_id = payout.batch_header.payout_batch_id
            batch.save()
            return {'status': 'Success',
                    'payout_batch_id': payout.batch_header.payout_batch_id}
        else:
            return {'status': 'Failed',
                    'error': payout.error}
    except Exception as e:
        return {'status': 'Failed',
                'error': e}


def get(batch):
    # TODO: delete this - for developing only
    paypalrestsdk.configure({
        "mode": "sandbox",  # sandbox or live
        "client_id": "AX3_V5iIbPLsEa_71d-pbfN2InBlMQPxTKqtwTMd1YxUxjxeIay75W6akP1ikLQ-4TpHMOoW7S-e5LOc",
        "client_secret": "EDuF-9rMsyA0PukAJ2BGNZingJ0GGsYoJ67hWTzRB9VtaBnaLRPLKSpYoIy25NjxEHZXZ7lYdZPh8v1B"})
    try:
        print('ID TO FIND::::', batch.payout_batch_id)
        payout = Payout.find(batch.payout_batch_id)
        return payout

    except ResourceNotFound as error:
        return 'error: nothing found! {}'.format(error)