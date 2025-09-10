import os

STARTED_STATUS = "STARTED"
FINISHED_STATUS = "FINISHED"

LIVE_STATUSES = [
    "In Progress", "Warmup", "Delayed Start", "Game Delayed",
    "Manager Challenge", "Review"
]

FINAL_STATUSES = [
    "Final", "Game Over", "Completed", "Completed Early"
]

SKIP_STATUSES = ["Postponed", "Cancelled", "Suspended"]

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MARINERS_ID = 136

HAPPY_GRIFFEY_EMOJI = "happygriffy" # "<:emoji_name:emoji_id>"
SAD_MS_PEPE_EMOJI = "sadMspepe"
FEELS_MS_MAN_EMOJI = "FeelsMsMan"

GOMS_GIF = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMTQzZnlxc3VpM3VsanFlMnRmb3IyaXN3MmNpZjdydTJmcTVsd2JpNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/OcldYrF5srXoY/giphy.gif"
BOOMS_GIF = "https://media1.tenor.com/m/KtMgRjTMS9oAAAAC/wanna-kill-myself-the-office.gif"
