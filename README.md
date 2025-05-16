🛠️ 1. Run the Container Interactively

Start the container in interactive mode so you can inspect things live:

docker run -it --rm mariners-discord-bot /bin/bash

This drops you into the shell inside the container. From there, try:

python bot.py

Now you’ll see any Python exceptions or print/debug output directly.
🧾 2. Add Logging or Print Statements

Add print() or logging.debug() in key spots of your script:

print("Bot is starting...")
print(f"Token is: {TOKEN}")
print("Game data fetched:", response)

Avoid using logging alone unless you configure it correctly — stdout is your friend in containers.