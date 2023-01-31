import re
from google_sheets_reader import GoogleSheetReader
from airtabler import Airtabler
import os

class MessageHandler:
    STATUS = {
        'NONE': 'NONE',
        'BAD_TWITTER_LINK': 'BAD_TWITTER_LINK',
        'DUPLICATE_RECORD': 'DUPLICATE_RECORD',
        'DB_SUCCESS': 'DB_SUCCESS',
        'DB_SAVING_ERROR': 'DB_SAVING_ERROR'
    }

    def __init__(self):
        self.status = MessageHandler.STATUS['NONE']

    def twitter_handle_match(self, message: str) -> str:
        match = re.search(r"twitter\.com\/(?P<twitter_handle>[a-zA-Z0-9_]+)", message)
        if match:
            return match.group("twitter_handle")

    def is_twitter_status(self, message: str) -> bool:
        pattern = r"^(https://twitter.com/|https://mobile.twitter.com/)(\w+)/status/(\d+)$"
        match = re.search(pattern, message)
        return bool(match)
    
    def url_match(self, url: str) -> str:
        match = re.search(r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)', url)
        if match:
            return match.group(0)

    def parse_launch_date(self, message: str, twitter_handle: str = None) -> str:
        if not twitter_handle:
            twitter_handle = self.twitter_handle_match(message)
        url = self.url_match(message)
        if not url:
            raise ValueError(f"There is not URL in this message: '{message}'")
        launch_date = message.replace(url, "")
        launch_date = re.sub(r"^[^a-z\d]*|[^a-z\d]*$", "", launch_date, flags=re.IGNORECASE)
        return launch_date

    async def handle(self, message: str, author: str):
        if not self.is_twitter_status(message):
            self.status = MessageHandler.STATUS["BAD_TWITTER_LINK"]
            return self.status
        twitter_handle = self.twitter_handle_match(message)
        if not twitter_handle:
            self.status = MessageHandler.STATUS["BAD_TWITTER_LINK"]
            return self.status
        twitter_link = f"https://twitter.com/{twitter_handle}"
        launch_date = self.parse_launch_date(message, twitter_handle)

        if not twitter_link:
            self.status = MessageHandler.STATUS["BAD_TWITTER_LINK"]
            return self.status

        if await self.does_record_exist(twitter_link, message):
            self.status = MessageHandler.STATUS["DUPLICATE_RECORD"]
            return self.status   
        airtabler = Airtabler()
        try:
            records = await airtabler.create_record(twitter_link, message, launch_date, author)
            if records and len(records) > 0:
                return MessageHandler.STATUS["DB_SUCCESS"]
        except Exception as err:
            if "NODE_ENV" not in os.environ or os.environ["NODE_ENV"] != "test":
                print("error saving to DB")
                print(err)
            return MessageHandler.STATUS["DB_SAVING_ERROR"]

    async def does_record_exist(self, twitter_link: str, message: str) -> bool:
        airtabler = Airtabler()
        profiles_records = await airtabler.find_profile_record(twitter_link)
        announcement_records = await airtabler.find_announcement_record(message)
        if announcement_records and len(announcement_records) > 0:
            return True
        if profiles_records and len(profiles_records) > 3:
            return True
        '''
        reader = GoogleSheetReader()
        lower_case_twitter = message.lower()
        sheet_entries = await reader.read_data()
        if sheet_entries and lower_case_twitter in sheet_entries:
            return True
        '''
        return False
