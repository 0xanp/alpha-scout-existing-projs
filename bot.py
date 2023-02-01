import discord
from discord.ext import commands
from message_handler import MessageHandler
import os
from dotenv import load_dotenv

load_dotenv()
client = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@client.event
async def on_ready():
    print("The bot is ready")

def message_username(message: discord.Message) -> str:
    return message.author.name + "#" + message.author.discriminator

EXAMPLES = "for example\nhttps://twitter.com/prometheansxyz/status/1619087210250371072?s=20&t=F-HswS5r0Rlck4V395TPvg\nor\nhttps://mobile.twitter.com/jollyswap/status/1605958314390474754?s=20&t=F-HswS5r0Rlck4V395TPvg\n\nIf you know the estimated launch date, you can add it after the twitter link, like \nhttps://twitter.com/zerodotfun/status/1604315597977706497?s=20&t=F-HswS5r0Rlck4V395TPvg December 20, 2022\nor\nhttps://mobile.twitter.com/CryptoDickbutts/status/1601029021331963905?s=20&t=F-HswS5r0Rlck4V395TPvg Q3 2023\nWe are currently only taking in 4 announcements per project per month"

@client.event
async def on_message(message):
    if message.author.bot:
        return
    handler = MessageHandler()
    result = await handler.handle(message.content, message_username(message))
    if result == MessageHandler.STATUS['BAD_TWITTER_LINK']:
        await message.channel.send(f":x: Invalid Format: Please enter the project Tweet link (i.e. it should start with https://www.twitter.com/twitter-username/status/)\n{EXAMPLES}")
    elif result == MessageHandler.STATUS['DB_SUCCESS']:
        await message.channel.send(":white_check_mark: Thank You! Successfully Saved")
    elif result == MessageHandler.STATUS['DUPLICATE_RECORD']:
        await message.channel.send(":x: That NFT project has already been added")
    elif result == MessageHandler.STATUS['DB_SAVING_ERROR']:
        await message.channel.send(":x: ERROR saving to the database, please contact an admin")

client.run(os.environ.get('DISCORD_BOT_TOKEN'))