from paypalrestsdk import Payout, ResourceNotFound, PayoutItem
from paypalrestsdk.exceptions import MissingConfig
import paypalrestsdk
import contextlib
from django.conf import settings


@contextlib.contextmanager
def PayPalClient(mode=settings.PAYPAL_MODE):
    try:
        yield paypalrestsdk.configure({
            "mode": mode,  # sandbox or live
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET,
        })
    except Exception as exc:
        print('PAYPAL ERROR: {err}'.format(err=exc))


def create(batch):
    with PayPalClient():
        try:
            payout = Payout(batch.batch_body)
            if payout.create():
                batch.payout_batch_id = payout.batch_header.payout_batch_id
                batch.save()
                return {'status': 'Success',
                        'payout_batch_id': payout.batch_header.payout_batch_id}
            else:
                return {'status': 'Failed',
                        'error_level': 'local',
                        'error': payout.error}
        except Exception as e:
            return {'status': 'Failed',
                    'error_level': 'global',
                    'error': e}


def get(payout_batch_id, header_only=False):
    with PayPalClient():
        try:

            if header_only:
                filter_fields = '&fields=batch_header'
            else:
                filter_fields = ''
            api = paypalrestsdk.api.default()

            payout = api.request(
                "https://api.sandbox.paypal.com/v1/payments/payouts/{}?total_required=true{}".format(payout_batch_id,
                                                                                                     filter_fields),
                "GET", {})

            # payout = Payout.find(batch.payout_batch_id)
            return payout

        except Exception as e:
            return {'error_status': 'Failed',
                    'error': e}


def get_payout_item(payout_item_id):
    with PayPalClient():
        try:
            payout_item = PayoutItem.find(payout_item_id)
            return payout_item

        except Exception as e:
            return {'error_status': 'Failed',
                    'error': e}
