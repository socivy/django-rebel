from typing import Type

from django_rebel.mail_templates import DjangoMailTemplate


class MailSentGroup:
    template_mail_sender: Type[DjangoMailTemplate] = None
    single_send_mode = True

    def get_mail_owners(self):
        raise NotImplementedError()

    def send_new_mails(self, count=None, force=False):
        mail_owners = self.get_mail_owners()

        if count is not None:
            mail_owners = mail_owners[:count]

        if self.single_send_mode:
            mails = []

            for mail_owner in mail_owners:
                mail = self.template_mail_sender(mail_owner).send(force=force)

                if mail:
                    mails.append(mail[0])
        else:
            mails = self.template_mail_sender(mail_owners).send(force=force)

        return mails
