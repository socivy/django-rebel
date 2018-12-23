import requests

from django_rebel.api.constants import EVENT_TYPES


class Response(dict):
    def __init__(self, mailgun, base_response: requests.Response, base_request: requests.PreparedRequest, **kwargs):
        from django_rebel.api.mailgun import Mailgun

        self.mailgun: Mailgun = mailgun
        self.base_request = base_request
        self.base_response = base_response
        self.extra_arguments = kwargs

        initial_data = self.get_initial_data()
        super(Response, self).__init__(**initial_data)

    def get_initial_data(self):
        return self.base_response.json()

    def resend_request(self):
        s = requests.Session()

        response = s.send(self.base_request)

        return self.__class__(base_response=response, base_request=self.base_request, **self.extra_arguments)


class MessageResponses:
    class SendResponse(Response):
        def message_id(self):
            return self["id"].replace("<", "").replace(">", "")
