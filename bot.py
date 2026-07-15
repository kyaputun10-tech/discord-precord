import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

credentials_dict = json.loads(
    os.getenv("GOOGLE_CREDENTIALS")
)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    credentials_dict,
    scope
)

client = gspread.authorize(creds)

sheet = client.open("稼働記録").sheet1
medal_sheet = client.open("稼働記録").worksheet("貯メダル")

bot = commands.Bot(
    command_prefix="!",
    intents=discord.Intents.default()
)


@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"{len(synced)}個のコマンドを同期")
    print("起動成功")


@bot.tree.command(
    name="record",
    description="稼働記録"
)
async def record(
    interaction: discord.Interaction,
    hall: str,
    machine: str,
    start: int,
    end: int,
    invest: int,
    payout: int
):

    diff = payout - invest

    # 貯メダル更新
    records_medal = medal_sheet.get_all_values()

    found = False
    new_total = diff

    for i, row in enumerate(records_medal[1:], start=2):

        if row[0] == hall:

            current = int(row[1])

            new_total = current + diff

            medal_sheet.update(
                f"B{i}",
                [[new_total]]
            )

            found = True
            break

    if not found:

        medal_sheet.append_row([
            hall,
            diff
        ])

        new_total = diff

    # 稼働記録保存
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        hall,
        machine,
        start,
        end,
        invest,
        payout,
        diff
    ])

    await interaction.response.send_message(
        f"""
📊 稼働記録

🏪 店舗: {hall}
🎰 機種: {machine}

開始G: {start}
終了G: {end}

投資: {invest}枚
回収: {payout}枚

差枚: {diff:+}枚

現在貯メダル: {new_total}枚
"""
    )


@bot.tree.command(
    name="today",
    description="本日の収支"
)
async def today(interaction: discord.Interaction):

    records = sheet.get_all_values()

    today_date = datetime.now().strftime("%Y-%m-%d")

    invest_total = 0
    payout_total = 0
    count = 0

    for row in records[1:]:

        if row[0].startswith(today_date):

            invest_total += int(row[5])
            payout_total += int(row[6])
            count += 1

    diff = payout_total - invest_total

    await interaction.response.send_message(
        f"""
📈 本日収支

稼働数: {count}台

総投資: {invest_total}枚
総回収: {payout_total}枚

差枚: {diff:+}枚
"""
    )


@bot.tree.command(
    name="month",
    description="今月の収支"
)
async def month(interaction: discord.Interaction):

    records = sheet.get_all_values()

    current_month = datetime.now().strftime("%Y-%m")

    invest_total = 0
    payout_total = 0
    count = 0

    for row in records[1:]:

        if row[0].startswith(current_month):

            invest_total += int(row[5])
            payout_total += int(row[6])
            count += 1

    diff = payout_total - invest_total

    await interaction.response.send_message(
        f"""
📅 今月の収支

稼働数: {count}台

総投資: {invest_total}枚
総回収: {payout_total}枚

差枚: {diff:+}枚
"""
    )


@bot.tree.command(
    name="hall",
    description="店舗別収支"
)
async def hall(
    interaction: discord.Interaction,
    hall: str
):

    records = sheet.get_all_values()

    invest_total = 0
    payout_total = 0
    count = 0

    for row in records[1:]:

        if row[1] == hall:

            invest_total += int(row[5])
            payout_total += int(row[6])
            count += 1

    diff = payout_total - invest_total

    await interaction.response.send_message(
        f"""
🏪 {hall}

稼働数: {count}台

総投資: {invest_total}枚
総回収: {payout_total}枚

差枚: {diff:+}枚
"""
    )


@bot.tree.command(
    name="medal",
    description="貯メダル一覧"
)
async def medal(interaction: discord.Interaction):

    records = medal_sheet.get_all_values()

    message = "🏦 貯メダル残高一覧\n\n"

    for row in records[1:]:
        message += f"{row[0]} : {row[1]}枚\n"

    await interaction.response.send_message(message)


bot.run(TOKEN)
