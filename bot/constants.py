import os

S3_BUCKET_NAME = "mariners-bot"
S3_OBJECT_KEY = "status.json"

STARTED_STATUS = "STARTED"
FINISHED_STATUS = "FINISHED"

FINAL_STATUSES = ["Final", "Game Over"]

# CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
MARINERS_ID = 136
# American League / AL West (statsapi division id) for standings after games
AL_LEAGUE_ID = 103
AL_WEST_DIVISION_ID = 200

HAPPY_GRIFFEY_EMOJI = "happygriffy"  # "<:emoji_name:emoji_id>"
SAD_MS_PEPE_EMOJI = "sadMspepe"
FEELS_MS_MAN_EMOJI = "FeelsMsMan"

GOMS_GIF = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExMTQzZnlxc3VpM3VsanFlMnRmb3IyaXN3MmNpZjdydTJmcTVsd2JpNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/OcldYrF5srXoY/giphy.gif"
BOOMS_GIF = "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHA0bzRmaTFoeHBjMThyYWpqeXJqZjdmbnQ3NG9oNTB0dms5NmtrZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/zGuiJzgLAYyHnRVKmD/giphy.gif"

GOMS_SWEEP_GIF = "https://klipy.com/gifs/looney-tunes-yosemite-sam-1"
BOOMS_SWEEP_GIF = "https://klipy.com/gifs/area51-aliens-1"
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
