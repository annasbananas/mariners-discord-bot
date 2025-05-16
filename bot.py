import discord
from discord.utils import get
import asyncio
from pytz import timezone
from constants import *
from utils import *

def setup_client():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    return discord.Client(intents=intents)

client = setup_client()

class StateManager():
    def __init__(self, client):
        self.client = client
        self.notified = {
            "start": set(),
            "final": set(),
        }
        self.channel = None

    async def add_custom_emoji_to_message(self, message, emoji_name):
        emoji = get(self.channel.guild.emojis, name=emoji_name)
        if emoji:
            message.add_reaction(emoji)

    async def check_statuses(self, status, game_id, mariners, opponent):
        # Check statuses
        self.game_started(status, game_id, mariners, opponent)
        self.game_finished(status, game_id, mariners, opponent)

    async def game_started(self, game_status, game_id, mariners_team, opponent_team):
        if game_status in LIVE_STATUSES and game_id not in self.notified["start"]:
            await self.channel.send(f"🚨 The game is about to start! {mariners_team['team']['name']} vs. {opponent_team['team']['name']} 🚨")
            self.notified["start"].add(game_id)

    async def game_finished(self, game_status, game_id, mariners_team, opponent_team):
        if game_status in FINAL_STATUSES and game_id not in self.notified["final"]:
            wins = mariners_team["leagueRecord"]["wins"]
            losses = mariners_team["leagueRecord"]["losses"]
            pct = mariners_team["leagueRecord"]["pct"]

            print(f"Final score: {mariners_team['score']} - {opponent_team['score']}. The Mariners are now {wins}-{losses} ({pct})")

            if mariners_team["score"] > opponent_team["score"]:
                message = await self.channel.send(f"🎉 GOMS! Final score - {mariners_team['team']['name']}: {mariners_team['score']} - {opponent_team['team']['name']}: {opponent_team['score']}. The Mariners are now {wins}-{losses} ({pct})")
                self.add_custom_emoji_to_message(message, HAPPY_GRIFFEY_EMOJI)
                await self.channel.send(GOMS_GIF)
            else:
                message = await self.channel.send(f"😞 BOOMS! Final score - {mariners_team['team']['name']}: {mariners_team['score']} - {opponent_team['team']['name']}: {opponent_team['score']}. The Mariners are now {wins}-{losses} ({pct})")
                self.add_custom_emoji_to_message(message, SAD_MS_PEPE_EMOJI)
                self.add_custom_emoji_to_message(message, FEELS_MS_MAN_EMOJI)
                await self.channel.send(BOOMS_GIF)
            self.notified["final"].add(game_id)

    async def check_game_loop(self):
        await self.client.wait_until_ready()
        self.channel = self.client.get_channel(CHANNEL_ID)
        while not self.client.is_closed():
            game, mariners, opponent = get_mlb_schedule_for_mariners()
            if game:
                # Deconstruct game_id and status
                game_id = game["gamePk"]
                status = game["status"]["detailedState"]
                print(f"Game's status: {status}")

                # Check game status and send corresponding message
                await self.check_statuses(status, game_id, mariners, opponent)

            print("Finished scan... waiting 10 minutes.")
            await asyncio.sleep(600)  # Check every 10 minutes

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    bot = StateManager(client)
    client.loop.create_task(bot.check_game_loop())

if __name__ == "__main__":
    client.run(TOKEN)

