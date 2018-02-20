# from otree.views.mturk import get_mturk_client
import boto3
from botocore.exceptions import NoCredentialsError, EndpointConnectionError

client = boto3.client('mturk')
# try:
print(client.get_account_balance())
# except EndpointConnectionError:
#     print('sorry no connection')

# myhit = client.get_hit(HITId='3UL5XDRDNC345UMVOW2KVR8NZYX585')

# send_bonus = client.send_bonus(
#     WorkerId='A5NHP0N1XC09K',
#     BonusAmount='3.0',
#     AssignmentId='3DY46V3X3Q3N5W0NG00J7RUEK7G55E',
#     Reason='Thanks for your patience! Good luck. Philipp',
#
# )
# print(send_bonus)
# print('=======')
#
# allP = client.list_bonus_payments(
#     # HITId='3UL5XDRDNC345UMVOW2KVR8NZYX585',
#     AssignmentId='3DY46V3X3Q3N5W0NG00J7RUEK7G55E',
# )
# print(allP)
print('=======')
