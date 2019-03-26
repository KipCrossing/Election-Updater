print("Flux Discord Bot")
import discord
from discord.ext import commands
import asyncio
from itertools import cycle
import os

from selenium import webdriver
import time
import pandas as pd


TOKEN = os.environ.get('DISCORD_BOT_TOKEN', None) # 'NTYwMDY3OTMyNDExOTIwMzg2.D3ujrQ.ZZc5cyGfwrNjvHKZ4tgSdSR1ZNg'

client = commands.Bot(command_prefix = '!')

async def update_score():
    await client.wait_until_ready()
    score = ''
    while not client.is_closed:
        try:
            driver = webdriver.Chrome()
            driver.get('https://vtr.elections.nsw.gov.au/lc/state/cc/fp_summary')
            
            # let it load; todo: does selenium have an await page load function?
            time.sleep(2)

            vtr_html = driver.page_source

            # extracts tables from html; group I is 9th -> index = 8
            df = pd.read_html(vtr_html)[8]
            

            new_score = df[list(df)[2]][16]
            percent_votes = df[list(df)[3]][16]
            driver.close()
        except Exception as e:
            print(e)
        if new_score != score:
            score = new_score
            print(score)
            await client.send_message(discord.Object('560067038349885441'), \
            "**UPDATE:** *Group Total* \nVotes: **{}** \n% of Votes: **{}**".format(str(score),str(percent_votes)))
        await asyncio.sleep(60)


client.loop.create_task(update_score())
client.run(TOKEN)
