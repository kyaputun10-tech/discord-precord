from flask import Flask
from threading import Thread
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

import discord
from discord.ext import commands

TOKEN = os.getenv("TOKEN")

app = Flask(__name__)

@app.route("/")
def home():
    return "Discord Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()

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
    user = interaction.user.name

    diff = payout - invest

    records_medal = medal_sheet.get_all_values()

    found = False
    new_total = diff

    for i, row in enumerate(records_medal[1:], start=2):

        if row[0] == user and row[1] == hall:

            current = int(row[2])

            new_total = current + diff

            medal_sheet.update(
                f"C{i}",
                [[new_total]]
            )

            found = True
            break

    if not found:

        medal_sheet.append_row([
            user,
            hall,
            diff
        ])

        new_total = diff
    # 稼働記録保存
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        user,
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

👤 ユーザー: {user}

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

    user = interaction.user.name

    invest_total = 0
    payout_total = 0
    count = 0

    for row in records[1:]:

        if row[0].startswith(today_date) and row[1] == user:

            invest_total += int(row[6])
            payout_total += int(row[7])
            count += 1

    diff = payout_total - invest_total

    await interaction.response.send_message(
        f"""
📈 本日収支

👤 ユーザー: {user}

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

    user = interaction.user.name

    records = sheet.get_all_values()

    current_month = datetime.now().strftime("%Y-%m")

    invest_total = 0
    payout_total = 0
    count = 0

    for row in records[1:]:

       if row[0].startswith(current_month) and row[1] == user:

            invest_total += int(row[6])
            payout_total += int(row[7])
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
    user = interaction.user.name

    records = sheet.get_all_values()

    invest_total = 0
    payout_total = 0
    count = 0

    for row in records[1:]:

        if row[1] == user and row[2] == hall:

            invest_total += int(row[6])
            payout_total += int(row[7])
            count += 1

    diff = payout_total - invest_total

    await interaction.response.send_message(
        f"""
🏪 {hall}

👤 ユーザー: {user}

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

    user = interaction.user.name

    records = medal_sheet.get_all_values()

    message = f"🏦 {user} の貯メダル残高\n\n"

    for row in records[1:]:

        if row[0] == user:

            message += f"🏪 {row[1]} : {row[2]}枚\n"

    await interaction.response.send_message(message)

bot.run(TOKEN)
