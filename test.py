import unittest
from unittest.mock import MagicMock, patch
from airtabler import Airtabler
from message_handler import MessageHandler
from google_sheets_reader import GoogleSheetReader
import asyncio

class TestAirtabler(unittest.TestCase):
    airtabler = Airtabler()
    ANNOUNCEMENT_RECORDS = ["https://twitter.com/Vince_Van_Dough/status/1595138009804206080",
                            "https://twitter.com/Vince_Van_Dough/status/1622399935042707456",
                            "https://twitter.com/Vince_Van_Dough/status/1622386264581226498",
                            "https://twitter.com/Vince_Van_Dough/status/1622252918123466752",
                            "https://twitter.com/0xAnP/status/25332523523532"
                            ]

    async def test_create_record(self):
        print("\nTESTING create_record...")
        for record in self.ANNOUNCEMENT_RECORDS:
            twitter_profile = "https://twitter.com/Vince_Van_Dough"
            author = "mintyMcMintable#9999"
            records = await self.airtabler.create_record(twitter_profile, record, author)
            result = records['fields']
            self.assertEqual(result["Twitter Profile"], twitter_profile)
            self.assertEqual(result["Announcement"], record)
            self.assertEqual(result["Author"], author)
        print("PASSED")

    async def test_find_announcement_record(self):
        print("\nTESTING find_record...")
        for record in self.ANNOUNCEMENT_RECORDS:
            records = await self.airtabler.find_announcement_record(record)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]['fields']["Announcement"], record)
        print("PASSED")

    async def test_find_profile_record(self):
        print("\nTESTING find_record...")
        profile = "https://twitter.com/Vince_Van_Dough"
        records = await self.airtabler.find_profile_record(profile)
        self.assertEqual(len(records), 5)
        self.assertEqual(records[0]['fields']["Twitter Profile"], profile)
        print("PASSED")
'''
class TestGoogleSheetReader(unittest.TestCase):
    async def test_read_data(self):
        print("\nTESTING google_sheets_reader...")
        reader = GoogleSheetReader()
        data = await reader.read_data()
        self.assertFalse("https://twitter.com/LonelyPopNFT" in data) # should not match since we called .lower()
        self.assertTrue("https://twitter.com/lonelypopnft" in data)
        self.assertTrue("https://twitter.com/metapeeps" in data)
        print("PASSED")
'''

class TestMessageHandler(unittest.TestCase):
    handler = MessageHandler()
    DUPLICATE_ANOUNCEMENTS = {"https://mobile.twitter.com/Vince_Van_Dough/status/1595138009804206080":"https://twitter.com/Vince_Van_Dough", # similar record 
                            "https://twitter.com/Vince_Van_Dough/status/1595138009804206080?s=20&t=HuZo8oFIRpxXnRkrYjRImQ":"https://twitter.com/Vince_Van_Dough", #similar record
                            "https://twitter.com/Vince_Van_Dough/status/43232322323":"https://twitter.com/Vince_Van_Dough", # not similar but exceed the limit of 4
                            "https://mobile.twitter.com/Vince_Van_Dough/status/4124124211241":"https://twitter.com/Vince_Van_Dough", # not similar but exceed the limit of 4
                            "https://twitter.com/0xAnP/status/25332523523532":"https://twitter.com/0xAnP/"
                            }
    async def test_does_record_exist(self):
        print("\nTESTING does_record_exist...")
        for announcement in self.DUPLICATE_ANOUNCEMENTS:
            exists = await self.handler.does_record_exist(self.DUPLICATE_ANOUNCEMENTS[announcement], announcement)
            self.assertTrue(exists)

        exists = await self.handler.does_record_exist("https://twitter.com/0xAnP/status/23534534534534","https://twitter.com/0xAnP")
        self.assertFalse(exists)

        print("PASSED")

    async def test_handle(self):
        author = 'mcMinty'
        print("\nTESTING DB status...")
        # BAD_TWITTER_LINK
        result = await self.handler.handle("moonbirds 2022", author)
        self.assertEqual(result, MessageHandler.STATUS['BAD_TWITTER_LINK'])

        # DUPLICATE_RECORD
        for announcement in self.DUPLICATE_ANOUNCEMENTS:
            result = await self.handler.handle(f"{announcement} 2022", author)
            print(announcement)
            self.assertEqual(result, MessageHandler.STATUS['DUPLICATE_RECORD'])

        # DB_SUCCESS
        twitter_link = "https://twitter.com/prometheansxyz/status/1611133847420403713?s=20&t=HuZo8oFIRpxXnRkrYjRImQ"
        result =  await self.handler.handle(twitter_link, author)
        self.assertEqual(result, MessageHandler.STATUS['DB_SUCCESS'])

        # DB_SAVING_ERROR
        with patch.object(Airtabler, 'create_record', MagicMock(side_effect=Exception("intentionally generated TEST Error"))):
            twitter_link = "https://twitter.com/prometheansxyz/status/3242423432423432"
            result = await self.handler.handle(f"{twitter_link} 2022", author)
            self.assertEqual(result, MessageHandler.STATUS['DB_SAVING_ERROR'])
        print("PASSED")

    def test_twitter_handle_match(self):
        print("\nTESTING twitter_handle_match...")
        
        # upper and lowercase
        print("Upper and Lowercase")
        message = "https://twitter.com/MoonbirdsXYZ/status/123424"
        self.assertEqual(self.handler.twitter_handle_match(message), "MoonbirdsXYZ")
        print("PASSED")

        # numbers and underscores
        print("Numbers and Underscores")
        message = "https://twitter.com/_Boonbirds99/status/123424"
        self.assertEqual(self.handler.twitter_handle_match(message), "_Boonbirds99")
        print("PASSED")

        # http not https
        print("http not https")
        message = "http://twitter.com/MoonbirdsXYZ/status/123424"
        self.assertEqual(self.handler.twitter_handle_match(message), "MoonbirdsXYZ")
        print("PASSED")
        
        # has no protocol https
        print("has no protocol https")
        message = "twitter.com/MoonbirdsXYZ/status/123424"
        self.assertEqual(self.handler.twitter_handle_match(message), "MoonbirdsXYZ")
        print("PASSED")
        
        # has mobile/www subdomain
        print("has mobile or www subdomain")
        message = "mobile.twitter.com/MoonbirdsXYZ/status/123424"
        self.assertEqual(self.handler.twitter_handle_match(message), "MoonbirdsXYZ")
        message = "www.twitter.com/MoonbirdsXYZ/status/123424"
        self.assertEqual(self.handler.twitter_handle_match(message), "MoonbirdsXYZ")
        print("PASSED")

        # has comma, period or bar delimiter
        print("has comma, period or bar delimiter")
        message = "https://twitter.com/_GoeyGeese1/status/123424,April 5, 2023"
        self.assertEqual(self.handler.twitter_handle_match(message), "_GoeyGeese1")
        message = "https://twitter.com/_GoeyGeese1/status/123424.April 5, 2023"
        self.assertEqual(self.handler.twitter_handle_match(message), "_GoeyGeese1")
        message = "https://twitter.com/_GoeyGeese1/status/123424|April 5, 2023"
        self.assertEqual(self.handler.twitter_handle_match(message), "_GoeyGeese1")
        print("PASSED")
        
        # has query string
        print("has query string")
        message = "https://mobile.twitter.com/Moonbirds55_?t=yUnZi2HaVMlwaSGs_Dyzxw&s=09,2023/status/123424"
        self.assertEqual(self.handler.twitter_handle_match(message), "Moonbirds55_")
        print("PASSED")

        # receives garbage
        print("receives garbage")
        message = "twat.com/NoNadaNothing"
        self.assertIsNone(self.handler.twitter_handle_match(message))
        message = "twitter.com"
        self.assertIsNone(self.handler.twitter_handle_match(message))
        message = "twitter.com/"
        self.assertIsNone(self.handler.twitter_handle_match(message))
        message = "twitter.com/"
        self.assertIsNone(self.handler.twitter_handle_match(message))
        message = "twitter.com/!!!"
        self.assertIsNone(self.handler.twitter_handle_match(message))
        print("PASSED")
    
    def test_is_twitter_status(self):
        print("\nTESTING is_twitter_status...")

        # with mobile
        message = "https://mobile.twitter.com/Vince_Van_Dough/status/1595138009804206080"
        self.assertTrue(self.handler.is_twitter_status(message))

        # regular desktop link
        message = "https://twitter.com/Vince_Van_Dough/status/1595138009804206080"
        self.assertTrue(self.handler.is_twitter_status(message))

        # random links
        message = "https://google.com"
        self.assertFalse(self.handler.is_twitter_status(message))

        message = "https://facebook.com"
        self.assertFalse(self.handler.is_twitter_status(message))

        # random words
        message = "hello, world!"
        self.assertFalse(self.handler.is_twitter_status(message))

        message = "wassup!!!!!"
        self.assertFalse(self.handler.is_twitter_status(message))

        # valid links followed by date
        message = "https://twitter.com/Vince_Van_Dough/status/1595138009804206080 Dec 5"
        self.assertTrue(self.handler.is_twitter_status(message))

        message = "https://mobile.twitter.com/Vince_Van_Dough/status/1595138009804206080 Q3, 2023"
        self.assertTrue(self.handler.is_twitter_status(message))

        print("PASSED")


    def test_tweet_status_id_match(self):
        print("\nTESTING tweet_status_id_match...")

        # desktop link followed by status id
        message = "https://twitter.com/Vince_Van_Dough/status/1595138009804206080"
        self.assertEqual(self.handler.tweet_status_id_match(message), "1595138009804206080")

        # mobile link followed by status id
        message = "https://mobile.twitter.com/Vince_Van_Dough/status/1595138009804206080"
        self.assertEqual(self.handler.tweet_status_id_match(message), "1595138009804206080")

        # desktop link followed by status id with query string
        message = "https://twitter.com/Vince_Van_Dough/status/1595138009804206080?s=20&t=HuZo8oFIRpxXnRkrYjRImQ"
        self.assertEqual(self.handler.tweet_status_id_match(message), "1595138009804206080")

        # mobile link followed by status id with query string
        message = "https://mobile.twitter.com/Vince_Van_Dough/status/1595138009804206080?s=20&t=HuZo8oFIRpxXnRkrYjRImQ"
        self.assertEqual(self.handler.tweet_status_id_match(message), "1595138009804206080")

        print("PASSED")

    def test_url_match(self):
        print("\nTESTING url_match...")
        # with date ending
        print("with date ending")
        url = "https://mobile.twitter.com/Moonbirds55_ April 5, 2023"
        self.assertEqual(self.handler.url_match(url), "https://mobile.twitter.com/Moonbirds55_")
        print("PASSED")

        # with query string and comma delimiter
        print("with query string and comma delimiter")
        url = "https://twitter.com/Moonbirds55_?t=yUnZi2HaVMlwaSGs_Dyzxw&s=09,April 5, 2023"
        self.assertEqual(self.handler.url_match(url), "https://twitter.com/Moonbirds55_?t=yUnZi2HaVMlwaSGs_Dyzxw&s=09")
        print("PASSED")

        # period will be included in url
        print("period delimiter will be included in url (unexpected!)")
        url = "https://www.twitter.com/Moonbirds55_?t=yUnZi2HaVMlwaSGs_Dyzxw&s=09.April 5, 2023"
        self.assertEqual(self.handler.url_match(url), "https://www.twitter.com/Moonbirds55_?t=yUnZi2HaVMlwaSGs_Dyzxw&s=09.April")
        print("PASSED")
    
    '''
    def test_parse_launch_date(self):
        print("\nTESTING parse_launch_date...")

        # space delimited
        print("space delimited")
        message = "https://twitter.com/_GoeyGeese1 2023"
        self.assertEqual(self.handler.parse_launch_date(message), "2023")
        print("PASSED")

        # space delimited with date and comma
        print("space delimited with date and comma")
        message = "https://twitter.com/_GoeyGeese1 April 5, 2023"
        self.assertEqual(self.handler.parse_launch_date(message), "April 5, 2023")
        print("PASSED")

        # comma delimited
        print("comma delimited")
        message = "https://twitter.com/_GoeyGeese1,2023"
        self.assertEqual(self.handler.parse_launch_date(message), "2023")
        print("PASSED")
        
        # url with query string and comma delimited
        print("url with query string and comma delimited")
        message = "https://mobile.twitter.com/Moonbirds55_?t=yUnZi2HaVMlwaSGs_Dyzxw&s=09,April 5, 2023"
        self.assertEqual(self.handler.parse_launch_date(message), "April 5, 2023")
        print("PASSED")

        # period delimited
        print("period delimited (unexpected!)")
        message = "https://mobile.twitter.com/Moonbirds55_?t=yUnZi2HaVMlwaSGs_Dyzxw&s=09.April 5, 2023"
        self.assertEqual(self.handler.parse_launch_date(message), "5, 2023")
        print("PASSED")
    '''

async def main():
    print("Testing Alpha Scout Bot...")
    # Testing airtabler
    airtabler_tester = TestAirtabler()
    await airtabler_tester.test_create_record()
    await airtabler_tester.test_find_announcement_record()
    await airtabler_tester.test_find_profile_record()
    '''
    # Testing google_sheets_reader
    google_sheets_reader_tester = TestGoogleSheetReader()
    await google_sheets_reader_tester.test_read_data()
    '''
    # Testing message_handler
    message_handler_tester = TestMessageHandler()
    await message_handler_tester.test_handle()
    await message_handler_tester.test_does_record_exist()
    message_handler_tester.test_url_match()
    message_handler_tester.test_is_twitter_status()
    message_handler_tester.test_tweet_status_id_match()
    #message_handler_tester.test_parse_launch_date()
    message_handler_tester.test_twitter_handle_match()
    print("\nDone Testing Alpha Scout Bot!")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
