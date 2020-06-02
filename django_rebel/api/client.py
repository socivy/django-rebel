import requests


class Client:
    DEFAULT_API_URL = "https://api.mailgun.net/v3"

    def __init__(self, mailgun):
        self.mailgun = mailgun

    def prepare_request(self, url: str, method="get", data=None, headers=None, params=None, **kwargs):
        real_url = "%s/%s/%s" % (self.get_api_url(), self.mailgun.profile_settings["API"]["DOMAIN"], url)

        auth = ("api", self.mailgun.profile_settings["API"]["API_KEY"])

        req = requests.Request(method=method,
                               url=real_url,
                               auth=auth,
                               data=data,
                               headers=headers,
                               params=params,
                               **kwargs)

        return req.prepare()

    def get_api_url(self):
        if "API_URL" in self.mailgun.profile_settings["API"].keys():
            return self.mailgun.profile_settings["API"]["API_URL"]

        return self.DEFAULT_API_URL
