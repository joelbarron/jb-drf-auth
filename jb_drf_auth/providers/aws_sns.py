import boto3

from jb_drf_auth.conf import get_setting
from jb_drf_auth.providers.base import BaseSmsProvider


class AwsSnsSmsProvider(BaseSmsProvider):
    def __init__(self):
        self.client = boto3.client("sns")

    def send_sms(self, phone_number: str, message: str):
        message_attributes = {
            "AWS.SNS.SMS.SMSType": {
                "DataType": "String",
                "StringValue": get_setting("SMS_TYPE"),
            }
        }
        sender_id = get_setting("SMS_SENDER_ID")
        if sender_id:
            message_attributes["AWS.SNS.SMS.SenderID"] = {
                "DataType": "String",
                "StringValue": sender_id,
            }

        return self.client.publish(
            PhoneNumber=phone_number,
            Message=message,
            MessageAttributes=message_attributes,
        )
