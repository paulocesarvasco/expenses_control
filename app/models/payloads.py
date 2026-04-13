class SearchResponsePayload():

    def __init__(self) -> None:
        self.store_name = ''
        self.purchase_date = ''
        self.total = 0.0
        self.purchases = []

    def to_dict(self):
        payload = dict()
        payload['store_name'] = self.store_name
        payload['purchase_date'] = self.purchase_date
        payload['total'] = self.total
        payload['purchases'] = self.purchases

        return payload
