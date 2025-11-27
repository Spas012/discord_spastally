import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Database setup
DB_FILE = 'tallies.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tallies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            UNIQUE(guild_id, name)
        )
    ''')
    conn.commit()
    conn.close()

# Bot setup
class TallyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)

    async def setup_hook(self):
        init_db()
        await self.tree.sync()
        print("Database initialized and commands synced.")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')

bot = TallyBot()

# Slash Commands

async def tally_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch tallies that match the current input (case-insensitive partial match)
    cursor.execute("SELECT name FROM tallies WHERE guild_id = ? AND name LIKE ?", (interaction.guild_id, f'%{current}%'))
    rows = cursor.fetchall()
    conn.close()
    
    return [
        app_commands.Choice(name=row['name'], value=row['name'])
        for row in rows
    ][:25] # Discord limits to 25 choices

@bot.tree.command(name="tally_create", description="Create a new tally")
@app_commands.describe(name="The name of the tally")
async def tally_create(interaction: discord.Interaction, name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO tallies (guild_id, name, count) VALUES (?, ?, ?)', (interaction.guild_id, name, 0))
        conn.commit()
        await interaction.response.send_message(f"Tally '{name}' created!", ephemeral=False)
    except sqlite3.IntegrityError:
        await interaction.response.send_message(f"Tally '{name}' already exists.", ephemeral=True)
    finally:
        conn.close()

async def perform_tally_add(interaction: discord.Interaction, name: str, amount: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tallies SET count = count + ? WHERE guild_id = ? AND name = ?', (amount, interaction.guild_id, name))
    if cursor.rowcount > 0:
        conn.commit()
        # Fetch new count
        cursor.execute('SELECT count FROM tallies WHERE guild_id = ? AND name = ?', (interaction.guild_id, name))
        new_count = cursor.fetchone()['count']
        await interaction.response.send_message(f"Added {amount} to '{name}'. New count: {new_count}", ephemeral=False)
    else:
        await interaction.response.send_message(f"Tally '{name}' not found.", ephemeral=True)
    conn.close()

@bot.tree.command(name="tally_add", description="Add to a tally")
@app_commands.describe(name="The name of the tally", amount="Amount to add (default 1)")
@app_commands.autocomplete(name=tally_autocomplete)
async def tally_add(interaction: discord.Interaction, name: str, amount: int = 1):
    await perform_tally_add(interaction, name, amount)

@bot.tree.command(name="tally", description="Quickly add 1 to a tally")
@app_commands.describe(name="The name of the tally")
@app_commands.autocomplete(name=tally_autocomplete)
async def tally_quick_add(interaction: discord.Interaction, name: str):
    await perform_tally_add(interaction, name, 1)

@bot.tree.command(name="tally_sub", description="Subtract from a tally")
@app_commands.describe(name="The name of the tally", amount="Amount to subtract (default 1)")
@app_commands.autocomplete(name=tally_autocomplete)
async def tally_sub(interaction: discord.Interaction, name: str, amount: int = 1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE tallies SET count = count - ? WHERE guild_id = ? AND name = ?', (amount, interaction.guild_id, name))
    if cursor.rowcount > 0:
        conn.commit()
        # Fetch new count
        cursor.execute('SELECT count FROM tallies WHERE guild_id = ? AND name = ?', (interaction.guild_id, name))
        new_count = cursor.fetchone()['count']
        await interaction.response.send_message(f"Subtracted {amount} from '{name}'. New count: {new_count}", ephemeral=False)
    else:
        await interaction.response.send_message(f"Tally '{name}' not found.", ephemeral=True)
    conn.close()

@bot.tree.command(name="tally_view", description="View a tally's count")
@app_commands.describe(name="The name of the tally")
@app_commands.autocomplete(name=tally_autocomplete)
async def tally_view(interaction: discord.Interaction, name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM tallies WHERE guild_id = ? AND name = ?', (interaction.guild_id, name))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        await interaction.response.send_message(f"Tally for {name} is at: {row['count']}", ephemeral=False)
    else:
        await interaction.response.send_message(f"Tally '{name}' not found.", ephemeral=True)

@bot.tree.command(name="tally_list", description="List all tallies")
async def tally_list(interaction: discord.Interaction):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name, count FROM tallies WHERE guild_id = ?', (interaction.guild_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        tally_list_str = "\n".join([f"**{row['name']}**: {row['count']}" for row in rows])
        await interaction.response.send_message(f"**Tallies:**\n{tally_list_str}", ephemeral=False)
    else:
        await interaction.response.send_message("No tallies found.", ephemeral=True)

@bot.tree.command(name="tally_delete", description="Delete a tally")
@app_commands.describe(name="The name of the tally")
@app_commands.autocomplete(name=tally_autocomplete)
async def tally_delete(interaction: discord.Interaction, name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tallies WHERE guild_id = ? AND name = ?', (interaction.guild_id, name))
    if cursor.rowcount > 0:
        conn.commit()
        await interaction.response.send_message(f"Tally '{name}' deleted.", ephemeral=False)
    else:
        await interaction.response.send_message(f"Tally '{name}' not found.", ephemeral=True)
    conn.close()

if __name__ == '__main__':
    if not TOKEN:
        print("Error: DISCORD_TOKEN not found in .env file.")
    else:
        bot.run(TOKEN)
