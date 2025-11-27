# Discord Tally Bot

Antigravity Discord Tally Bot.
This entire code was AI generated. I have done literally nothing.

A robust, self-hosted Discord bot for tracking "tallies" (event counters) within a server. Built with Python and SQLite.

## Features

*   **Self-Hosted & Persistent:** Uses a local SQLite database (`tallies.db`).
*   **Slash Commands:** Modern Discord interaction using `/` commands.
*   **Container Friendly:** Stateless code logic with file-based persistence (easy to mount as a volume).
*   **Secure:** Uses `.env` for token management.

## Prerequisites

*   Python 3.8 or higher
*   A Discord Bot Token

## Permissions

When inviting the bot to your server, ensure you select the following:

### OAuth2 Scopes
*   `bot`
*   `applications.commands` (Critical for Slash Commands)

### Bot Permissions
*   `Send Messages` (To reply to commands)
*   `View Channels`

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd antigravity_discord
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration:**
    Create a `.env` file in the root directory (or rename the provided template):
    ```bash
    echo "DISCORD_TOKEN=your_actual_token_here" > .env
    ```

## Usage

Run the bot:
```bash
python main.py
```

### Commands

*   `/tally [name]`: Quickly add 1 to a tally.
*   `/tally_create [name]`: Create a new tally (starts at 0).
*   `/tally_add [name] [amount]`: Add to a tally (default 1).
*   `/tally_sub [name] [amount]`: Subtract from a tally (default 1).
*   `/tally_view [name]`: View the current count of a tally.
*   `/tally_list`: List all tallies in the server.
*   `/tally_delete [name]`: Permanently delete a tally.

> **Note:** Commands that require a tally name now support autocomplete! Just start typing to see suggestions.

## Database

The bot will automatically create a `tallies.db` file in the root directory upon the first run. If running in a Docker container, ensure this file (or the directory) is mounted to a volume to persist data across restarts.
