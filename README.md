# sync-osu-names-to-discord

A comprehensive script that use three-way diffs to synchronize osu! usernames to
a Discord server.

The script looks up the username of all members of a Discord server on osu!, if
it finds an osu! profile with the same name, it will associate their Discord ID
and osu! ID in a save file.

On subsequent runs, the script is capable of updating the Discord nickname of
the user if their osu! username changed.

If desired, the script can report drifts in a Discord channel instead of fixing
them itself, if a manual workflow is prefered.

## Running

The script can be run using Python or the built container images can be used
with your preferred container runtime, such as Docker.

If running via Python, you may need to install the requirements listed in
`requirements.txt` first. The recommended way is to use a virtual environment,
for example:

```bash
python -m venv
source .venv/bin/activate
pip install -r requirements.txt

python main.py --help
```

The script was only tested with Python 3.14 and on Linux. Please file issues if
you need support for your environment.

The script requires some variables, you can set them as environment variable, or
in a `.env` file in the current directory, or as CLI arguments
(`DISCORD_SERVER_ID` becomes `--discord-server-id`).

⚠️: Avoid passing secret (such as bot tokens) as CLI arguments, they can leak in
your shell history or be stolen by listing all running processes.

<!-- MARK: Config vars -->

| Variable | Type | Default | Description |
| --- | --- | --- | --- |
| `DISCORD_SERVER_ID` | `str` | *(required)* | Server in which the nicknames must sync |
| `DISCORD_BOT_TOKEN` | `str` | *(required)* | Token from a bot that can read members and change nicknames on the server |
| `DISCORD_WEBHOOK` | `str \| None` | `None` | Webhook URL to send the report to |
| `DB_PATH` | `str` | `'save.json'` | Path to the JSON file in which the data is stored |
| `APPLY_NICKNAME` | `bool` | `True` | Whether to apply the nickname changes on Discord or just report them |
| `LOOP_MINUTES` | `float` | `0` | If > 0, the program will run in a loop and repeat the process every given minutes |
| `SEND_REPORT` | `bool` | `True` | Whether to send a status report or just do the actions without reporting |

<!-- ENDMARK -->

## License

MIT.
