import json
from typing import Union

import requests
from robot.api.deco import library

from qbrix.core.qbrix_robot_base import QbrixRobotTask
from qbrix.tools.shared.qbrix_authentication import get_secure_setting


@library(scope="GLOBAL", auto_keywords=True, doc_format="reST")
class QbrixSlack(QbrixRobotTask):

    """Slack Keywords for Robot"""

    def slack_message_using_webhook(
        self,
        webhook_url: str,
        channel: str,
        sender: str,
        text: str,
        icon_emoji: str = None,
        use_secure_setting=True,
    ):
        """Send message to Slack channel using webhook.

        Args:
            webhook_url (str): If use_secure_message is True (The default) then this should be the name of the secure message entry from Q Labs which holds the slack webhook URL. Otherwise this is the Slack webhook URL.
            channel: channel needs to exist in the Slack server
            sender: shown in the message post as sender
            text: text for the message post
            icon_emoji: icon for the message post, defaults to None
            use_secure_setting (bool): If True (the default) then this will lookup the webhook_url by name from Q labs, using the value passed in for the webhook url. Otherwise will use the given value for the webhook url as the webhook url in the request.
        """
        headers = {"Content-Type": "application/json"}
        payload = {
            "channel": channel if "#" in channel else f"#{channel}",
            "username": sender,
            "text": text,
        }
        if icon_emoji:
            payload["icon_emoji"] = icon_emoji

        if use_secure_setting:
            webhook_url = get_secure_setting(webhook_url)

        response = requests.post(
            webhook_url, headers=headers, data=json.dumps(payload), timeout=60
        )
        print(response.status_code)

    def slack_raw_message(
        self,
        webhook_url: str,
        message: Union[str, dict],
        channel: str = None,
        use_secure_setting=True
    ):
        """Send Slack message by custom JSON content.

        Args:
            webhook_url (str): If use_secure_message is True (The default) then this should be the name of the secure message entry from Q Labs which holds the slack webhook URL. Otherwise this is the Slack webhook URL.
            channel: channel needs to exist in the Slack server
            message: dictionary or string defining message content and structure
            use_secure_setting (bool): If True (the default) then this will lookup the webhook_url by name from Q labs, using the value passed in for the webhook url. Otherwise will use the given value for the webhook url as the webhook url in the request.
        """
        headers = {"Content-Type": "application/json"}

        if use_secure_setting:
            webhook_url = get_secure_setting(webhook_url)

        if channel and isinstance(message, dict):
            message["channel"] = channel
        elif channel:
            self.builtin.log_to_console(
                "\nCan't set channel as 'json_data' is a string."
            )
            return

        data_for_message = message if isinstance(message, str) else json.dumps(message)
        response = requests.post(
            webhook_url, headers=headers, data=data_for_message, timeout=60
        )
        print(response.status_code)
