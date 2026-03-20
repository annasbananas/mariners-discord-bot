🛠️ 1. Run the Container Interactively

Building the container:
`docker build --no-cache -t mariners-discord-bot-lambda .`

Start the container in interactive mode so you can inspect things live:

```
docker run --rm -p 9000:8080 --env-file .env \
  -e LOG_LEVEL=INFO \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN \
  -e AWS_REGION=us-east-1 \
  mariners-discord-bot-lambda
```

This drops you into the shell inside the container. From there, try:

`python bot.py`

Now you’ll see any Python exceptions or print/debug output directly.
🧾 2. Add Logging or Print Statements

Add print() or logging.debug() in key spots of your script:

```python
print("Bot is starting...")
print(f"Token is: {TOKEN}")
print("Game data fetched:", response)
```

Avoid using logging alone unless you configure it correctly — stdout is your friend in containers.

### Logging

The Lambda now uses standard Python logging with a shared config.

- Default level is `INFO`
- Override with `LOG_LEVEL` (for example: `DEBUG`, `WARNING`, `ERROR`)

Example:

```bash
docker run --rm -p 9000:8080 --env-file .env \
  -e LOG_LEVEL=DEBUG \
  -e AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY \
  -e AWS_SESSION_TOKEN \
  -e AWS_REGION=us-east-1 \
  mariners-discord-bot-lambda
```