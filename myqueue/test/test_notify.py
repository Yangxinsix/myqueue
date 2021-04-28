import smtplib


class SMTP:
    def __call__(self, host):
        return self

    def sendmail(self, fro, to, data):
        self.data = data


def test_notify(mq, monkeypatch):
    smtp = SMTP()
    monkeypatch.setattr(smtplib, 'SMTP', smtp)
    mq('submit ...')