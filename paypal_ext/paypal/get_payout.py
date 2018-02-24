from collections import namedtuple


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

    def get_items(self):
        return [(v,k) for k,v in self.items()]


inner_statuses_dict = {
    'UNPAID': 0,
    'PAID': 1,
    'PROCESSING': 2
}

a = AttrDict(inner_statuses_dict)
print(a.get_items())
print(a.PAID)
#
# class BATCH_STATUSES(Status):
#     UNPROCESSED = 0
#     SUCCESS = 1
#     FAILED = 2
