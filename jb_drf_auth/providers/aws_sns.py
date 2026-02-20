import boto3

from jb_drf_auth.conf import get_setting
from jb_drf_auth.providers.base import BaseSmsProvider


class AwsSnsSmsProvider(BaseSmsProvider):
    def __init__(self):
        client_kwargs = {}

        region = get_setting("AWS_REGION")
        if region:
            client_kwargs["region_name"] = region

        access_key_id = get_setting("AWS_ACCESS_KEY_ID")
        secret_access_key = get_setting("AWS_SECRET_ACCESS_KEY")
        session_token = get_setting("AWS_SESSION_TOKEN")
        endpoint_url = get_setting("AWS_SNS_ENDPOINT_URL")

        if access_key_id and secret_access_key:
            client_kwargs["aws_access_key_id"] = access_key_id
            client_kwargs["aws_secret_access_key"] = secret_access_key
        if session_token:
            client_kwargs["aws_session_token"] = session_token
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        self.client = boto3.client("sns", **client_kwargs)

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
