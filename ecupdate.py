print("Flux Discord Bot")
import asyncio
from itertools import cycle
import os
import time
import sys

import discord
from discord.ext import commands
from selenium import webdriver
import pandas as pd
from bs4 import BeautifulSoup


TOKEN = os.environ.get('DISCORD_BOT_TOKEN', None)
DISCORD_ROOM = os.environ.get('DISCORD_ROOM', '560067038349885441')
client = commands.Bot(command_prefix = '!')
print('loaded client')


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
    chrome_opts = webdriver.ChromeOptions()
    chrome_opts.add_argument('--headless')
    chrome_opts.add_argument('--no-sandbox')
    chrome_opts.add_argument('--disable-dev-shm-usage')
    try:
        driver = webdriver.Chrome(chrome_options=chrome_opts)
    except Exception as e:
        driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', chrome_options=chrome_opts)
    driver.get('https://vtr.elections.nsw.gov.au/lc/state/cc/fp_summary')

    # let it load; todo: does selenium have an await page load function?
    # let it be a long wait because better than failing
    time.sleep(2)

    # html of page; after it's been modified by JS
    vtr_html = driver.page_source
    vtr_soup = BeautifulSoup(vtr_html, 'html.parser')

    # don't need this anymore
    driver.close()

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

    quotas_f = float(quotas)
    max_quota = float(get_stored_value('max_quotas', '0'))
    if quotas_f > max_quota:
      set_stored_value('max_quotas', str(quotas))

    discord_msg = f"\n Votes: **{new_votes}** \n Primary pct: **{percent_votes}** (goal: 0.5%) \n Quotas: **{quotas}** (PB: {max_quota}) \n NSWEC progress: **{pct_votes_counted}** \n {last_updated}"
    print(discord_msg)
    set_stored_value('last_discord_msg', discord_msg)

    set_stored_value(f'log_{int(time.time())}', '\n-----\n'.join(map(str, [discord_msg, new_votes, percent_votes, quotas, last_updated, quota_votes])), subdir='log')

    await client.send_message(discord.Object(DISCORD_ROOM), discord_msg)


async def update_score():
    await client.wait_until_ready()
    # inf loop
    while True:
      try:
        await update_votes_inner()
        await asyncio.sleep(58)
      except Exception as e:
        print('Got exception')
        print(e)
        import traceback
        traceback.print_tb(e.__traceback__)
        print("\n\nwaiting 10s and trying again")
        await asyncio.sleep(10)


@client.command()
async def nswcount():
    with open('__last_discord_msg__.txt', 'r') as f:
        await client.say(f.read())


client.loop.create_task(update_score())
client.run(TOKEN)
