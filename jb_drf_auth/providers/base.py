class BaseSmsProvider:
    def send_sms(self, phone_number: str, message: str):
        raise NotImplementedError
