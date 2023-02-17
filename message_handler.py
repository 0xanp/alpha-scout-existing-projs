import re
from google_sheets_reader import GoogleSheetReader
from airtabler import Airtabler
import os

class MessageHandler:
    STATUS = {
        'NONE': 'NONE',
        'BAD_TWITTER_LINK': 'BAD_TWITTER_LINK',
        'NOT_FROM_NFT_LIST': 'NOT_FROM_NFT_LIST',
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
        pattern = r"^(https://twitter.com/|https://mobile.twitter.com/)(\w+)/status/*"
        match = re.search(pattern, message)
        return bool(match)
    
    def tweet_status_id_match(self, message):
        return message.split('/')[-1].split('?')[0]

    def url_match(self, url: str) -> str:
        match = re.search(r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)', url)
        if match:
            return match.group(0)
    
    def parse_comment(self, message: str, twitter_handle: str = None) -> str:
        if not twitter_handle:
            twitter_handle = self.twitter_handle_match(message)
        url = self.url_match(message)
        if not url:
            raise ValueError(f"There is not URL in this message: '{message}'")
        comment = message.replace(url, "")
        comment = re.sub(r"^[^a-z\d]*|[^a-z\d]*$", "", comment, flags=re.IGNORECASE)
        return comment
    
    async def is_notable(self, twitter_link):
        reader = GoogleSheetReader()
        lower_case_twitter = twitter_link.lower()
        sheet_entries = await reader.read_data()
        if sheet_entries and lower_case_twitter in sheet_entries:
            return True
        return False

    async def handle(self, message: str, author: str):
        message = self.url_match(message)
        if not message:
            self.status = MessageHandler.STATUS["BAD_TWITTER_LINK"]
            return self.status
        
        if not self.is_twitter_status(message):
            self.status = MessageHandler.STATUS["BAD_TWITTER_LINK"]
            return self.status

        twitter_handle = self.twitter_handle_match(message)
        if not twitter_handle:
            self.status = MessageHandler.STATUS["BAD_TWITTER_LINK"]
            return self.status

        twitter_profile = f"https://twitter.com/{twitter_handle.lower()}"
        comment = self.parse_comment(message, twitter_handle)

        if not await self.is_notable(twitter_profile):
            self.status = MessageHandler.STATUS["NOT_FROM_NFT_LIST"]
            return self.status

        status_id = self.tweet_status_id_match(message)
        annoucement = f"{twitter_profile}/status/{status_id}"
        
        if await self.does_record_exist(twitter_profile, annoucement):
            self.status = MessageHandler.STATUS["DUPLICATE_RECORD"]
            return self.status   
        airtabler = Airtabler()
        try:
            records = await airtabler.create_record(twitter_profile, annoucement, author, comment)
            if records and len(records) > 0:
                return MessageHandler.STATUS["DB_SUCCESS"]
        except Exception as err:
            if "NODE_ENV" not in os.environ or os.environ["NODE_ENV"] != "test":
                print("error saving to DB")
                print(err)
            return MessageHandler.STATUS["DB_SAVING_ERROR"]

    async def does_record_exist(self, twitter_profile: str, annoucement: str) -> bool:
        airtabler = Airtabler()
        profiles_records = await airtabler.find_profile_record(twitter_profile)
        announcement_records = await airtabler.find_announcement_record(annoucement)
        if announcement_records and len(announcement_records) > 0:
            return True
        if profiles_records and len(profiles_records) > 3:
            return True

        return False
