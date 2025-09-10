import discord
from discord.utils import get
import asyncio
from constants import *
from utils import *
from file_manager import get_status_from_file, save_status_to_file, generate_cached_status

def setup_client():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    return discord.Client(intents=intents)

client = setup_client()

class MarinersDiscordBot():
    def __init__(self, client):
        self.client = client
        self.channel = None
        self.cached_status = get_status_from_file()

    async def add_custom_emoji_to_message(self, message, emoji_name):
        """Adds a custom emoji to a Discord message."""
        emoji = get(self.channel.guild.emojis, name=emoji_name)
        if emoji:
            print(f"Adding {emoji_name} emoji to message...")
            await message.add_reaction(emoji)

    def update_cache(self, game_id, game_status, message_status):
        new_cached_status = generate_cached_status(game_id, game_status, message_status)
        save_status_to_file(new_cached_status)
        self.cached_status = new_cached_status

    async def check_statuses(self, status, game_id, mariners, opponent):
        """
        Checks the game status and determines whether a message should be sent or not.
        Currently sends messages when the game is about to start and when it finishes. 
        This bot uses a simplified version of the status from MLB's website to track if either message has been sent.
        """

        simplified_status = None
        if status in LIVE_STATUSES:
            simplified_status = STARTED_STATUS
        elif status in FINAL_STATUSES:
            simplified_status = FINISHED_STATUS
        else:
            return
        
        if (
            simplified_status == STARTED_STATUS and 
            self.cached_status.get("game_id") != game_id and
            self.cached_status.get("last_simplified_status_sent") != STARTED_STATUS
        ):
            await self.game_started(status, game_id, mariners, opponent)
            return

        if (
            simplified_status == FINISHED_STATUS and 
            self.cached_status.get("game_id") != game_id and
            self.cached_status.get("last_simplified_status_sent") != FINAL_STATUSES
        ):
            await self.game_finished(status, game_id, mariners, opponent)
            return

    async def game_started(self, game_status, game_id, mariners_team, opponent_team):
        """
        Checks if game has started and sends a message when it is about to start
        """
        if game_status in LIVE_STATUSES:
            await self.channel.send(f"🚨 The game is about to start! {mariners_team['team']['name']} vs. {opponent_team['team']['name']} 🚨")
            self.update_cache(game_id, game_status, STARTED_STATUS)


    async def game_finished(self, game_status, game_id, mariners_team, opponent_team):
        """
        Checks if game has finished and sends a message when it is over
        """
        if game_status in FINAL_STATUSES:
            wins = mariners_team["leagueRecord"]["wins"]
            losses = mariners_team["leagueRecord"]["losses"]
            pct = mariners_team["leagueRecord"]["pct"]

            print(f"Final score: {mariners_team['score']} - {opponent_team['score']}. The Mariners are now {wins}-{losses} ({pct})")

            if mariners_team["score"] > opponent_team["score"]:
                message = await self.channel.send(f"🎉 GOMS! Final score - {mariners_team['team']['name']}: {mariners_team['score']} - {opponent_team['team']['name']}: {opponent_team['score']}. The Mariners are now {wins}-{losses} ({pct})")
                await self.add_custom_emoji_to_message(message, HAPPY_GRIFFEY_EMOJI)
                await self.channel.send(GOMS_GIF)
            else:
                message = await self.channel.send(f"😞 BOOMS! Final score - {mariners_team['team']['name']}: {mariners_team['score']} - {opponent_team['team']['name']}: {opponent_team['score']}. The Mariners are now {wins}-{losses} ({pct})")
                await self.add_custom_emoji_to_message(message, SAD_MS_PEPE_EMOJI)
                await self.add_custom_emoji_to_message(message, FEELS_MS_MAN_EMOJI)
                await self.channel.send(BOOMS_GIF)

            self.update_cache(game_id, game_status, FINISHED_STATUS)


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
    bot = MarinersDiscordBot(client)
    client.loop.create_task(bot.check_game_loop())

if __name__ == "__main__":
    client.run(TOKEN)

