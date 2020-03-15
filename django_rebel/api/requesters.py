import json
from json import JSONDecodeError
from typing import Type

import requests
from requests import HTTPError

from django_rebel.exceptions import TargetMissing, RebelAPIError, RebelNotValidAddress

from .responses import Response, MessageResponses


class AbstractRequester:
    def __init__(self, mailgun):
        from .mailgun import Mailgun

        self.mailgun: Mailgun = mailgun

    def _get_response(self, response_class: Type[Response], prepared_request: requests.PreparedRequest, **kwargs):
        s = requests.Session()

        response = s.send(prepared_request)

        try:
            response.raise_for_status()
        except HTTPError as e:
            try:
                error_content = e.response.json()

                if "message" in error_content.keys():
                    if "is not a valid address" in error_content["message"]:
                        raise RebelNotValidAddress(request=e.request, response=e.response)
            except JSONDecodeError:
                """
                If there is json decode error, then skip
                """

            raise RebelAPIError(request=e.request, response=e.response)

        return response_class(base_response=response, base_request=prepared_request, mailgun=self.mailgun, **kwargs)


class Message(AbstractRequester):
    def send(self, subject: str, from_address: str = None, to=None, bcc=None, cc=None, text=None, html=None,
             variables=None, tags: list = None, test_mode: bool = None, inlines: list = None, attachments: list = None):

        if to is None and bcc is None and cc is None:
            raise TargetMissing()

        if from_address is None:
            from_address = self.mailgun.profile_settings["EMAIL"]

        if test_mode is None:
            test_mode = self.mailgun.settings["TEST_MODE"]

        if variables:
            variables = json.dumps(variables)

        data = {
            "from": from_address,
            "subject": subject,
            "text": text,
            "html": html,
            "o:tag": tags,
            "o:testmode": test_mode,
            "recipient-variables": variables
        }

        if to:
            data["to"] = to
        else:
            to = []

        if cc:
            data["cc"] = cc
        else:
            cc = []

        if bcc:
            data["bcc"] = bcc
        else:
            bcc = []

        sent_mails = to + cc + bcc

        files = []

        if inlines:
            files = [('inline', _f) for _f in inlines]

        if attachments:
            files = [('attachment', _f) for _f in attachments]

        req = self.mailgun.client().prepare_request("messages", method="post", data=data, files=files)

        response: MessageResponses.SendResponse = self._get_response(MessageResponses.SendResponse, req,
                                                                     sent_mails=sent_mails)

        return response


class Event(AbstractRequester):
    def list(self, message_id=None, event=None, email_list=None):
        params = {}

        if message_id:
            params["message-id"] = message_id

        if event:
            params["event"] = event

        if email_list:
            params["list"] = email_list

        req = self.mailgun.client().prepare_request("events", params=params)

        response: Response = self._get_response(Response, req)

        return response
