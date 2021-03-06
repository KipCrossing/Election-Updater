print("Flux Discord Bot")
import asyncio
from itertools import cycle
import os
import time
import sys
from collections import defaultdict

import aiohttp
import discord
from discord.ext import commands
#from selenium import webdriver
#from selenium.webdriver.firefox.options import Options
import pandas as pd
from bs4 import BeautifulSoup


TOKEN = os.environ.get('DISCORD_BOT_TOKEN', None)
DISCORD_ROOM = os.environ.get('DISCORD_ROOM', '560067038349885441')
#Max can you add the new channel ID to your DISCORD_DEV_ROOM
DEV_ROOM = os.environ.get('DISCORD_DEV_ROOM', '562605716591083560')
client = commands.Bot(command_prefix = '!')
star_emoji = '🌟'
print(f'loaded client {star_emoji}')

#opts = Options()
#opts.add_argument('--headless')
#driver = webdriver.Firefox(executable_path=f'{os.environ.get("PWD")}/geckodriver')


async def get_req(url, is_json=False):
  async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
      if is_json:
        return await response.json()
      return await response.text()


def get_stored_value(name, default=None):
  fname = f'__{name}__.txt'
  try:
    with open(fname, 'r') as f:
      contents = str(f.read())
      if len(contents) > 0:
        return contents
      return default
  except Exception as e:
    print(f'[INFO] FYI get_stored_value got exception: {str(e)}')
    return default


def set_stored_value(name, val, subdir=None):
  fname = f'__{name}__.txt'
  if subdir is not None:
    fname = f'{subdir}/{fname}'
  with open(fname, 'w+') as f:
    f.write(val)


async def update_votes_inner():
    stars = defaultdict(lambda: '')

    driver_load_start = time.time()

    vtr_meta_url = f'https://vtr.elections.nsw.gov.au/vtr.json?_={time.time() * 1000 // 1}'
    vtr_json = (await get_req(vtr_meta_url, is_json=True))["azure"]
    vtr_html_url = f'https://{vtr_json["id"]}.{vtr_json["type"]}.core.windows.net/{vtr_json["share"]}/lc/state/cc/fp_summary_report.html{vtr_json["storage"]}'
    vtr_html = await get_req(vtr_html_url)
    vtr_soup = BeautifulSoup(vtr_html, 'html.parser')
    report_content = vtr_soup.find(id="ReportContent")
    # p tags in report_content
    report_ps = report_content.find_all("p")
    last_updated = report_ps[0].string

    # check last updated; create file using a+ first if need be
    cached_updated = get_stored_value('last_updated_tag')
    if cached_updated == last_updated:
      print('no updates', time.time())
      return
    else:
      print("diff:", cached_updated, last_updated, sep='|\n')
    set_stored_value('last_updated_tag', last_updated)

    # grab the number of votes per quota
    quota_votes = int(list(report_ps[2].strings)[1].replace(',',''))
    # a quota is 4.55% or so; we can use this to figure out pct votes counted
    final_quota_votes = 5 * 10**6 * 0.0455
    # the // thing here will round to 2 dps
    pct_votes_counted = f'{(quota_votes * 10000 // final_quota_votes ) / 100} %'

    print(last_updated, quota_votes, sep=" | ")

    # extracts tables from html; group I is 9th -> index = 8
    flux_group_table_headings = pd.read_html(vtr_html)[8]
    hdrs = list(flux_group_table_headings)[2:5]
    hdr_votes, hdr_votes_pct, hdr_votes_quota = hdrs

    # get last row; total votes and quotas
    new_votes, percent_votes, quotas = [flux_group_table_headings[hdr][16] for hdr in hdrs]
    print(new_votes, percent_votes, quotas, sep=" | ")
    percent_votes = f'{new_votes * 100000 // quota_votes / 1000 * 0.0455:.3f} %'

    quotas_f = float(quotas)
    max_quota = float(get_stored_value('max_quotas', '0'))
    if quotas_f > max_quota:
      stars['quota'] = star_emoji
      set_stored_value('max_quotas', str(quotas))

    discord_msg = f"\n Votes: **{new_votes}** \n Primary pct: **{percent_votes}** (goal: 0.5%) \n Quotas: **{quotas}** (PB: {max_quota}){stars['quota']} \n NSWEC progress: **{pct_votes_counted}** \n __{last_updated}__"
    print(discord_msg)
    set_stored_value('last_discord_msg', discord_msg)

    set_stored_value(f'log_{int(time.time())}', '\n-----\n'.join(map(str, [discord_msg, new_votes, percent_votes, quotas, last_updated, quota_votes])), subdir='log')

    await client.send_message(discord.Object(DISCORD_ROOM), discord_msg)


async def update_score():
    await client.wait_until_ready()
    # await client.send_message(discord.Object(DEV_ROOM), f"Election Updater Bot started")
    # loop; 10m
    for i in range(10):
      print("starting update_score attempt")
      try:
        await update_votes_inner()
        await asyncio.sleep(53)
      except (KeyboardInterrupt, SystemExit) as e:
        await client.send_message(discord.Object(DEV_ROOM), f"E.U. Bot got keyboard interrupt / exit signal")
        break
        raise e
      except Exception as e:
        print(f'Got exception: {str(e)}')
        print(e)
        import traceback
        traceback.print_tb(e.__traceback__)
        await client.send_message(discord.Object(DEV_ROOM), f"E.U. bot exception: {str(e)}")
        print("\n\nwaiting 10s and trying again")
        await asyncio.sleep(10)
        print("await done")
    await client.close()
    asyncio.get_event_loop().stop()


@client.command()
async def nswcount():
    with open('__last_discord_msg__.txt', 'r') as f:
        await client.say(f.read())


try:
  client.loop.create_task(update_score())
  client.run(TOKEN)
finally:
  asyncio.new_event_loop().run_until_complete(client.close())
  #driver.close()
  #driver.quit()

