"""
Example Discord bot demonstrating sharding with RustCord

Sharding is necessary when a bot exceeds 2500 guilds.
Each shard handles a subset of the guilds based on the formula:
    guild_id % shard_count = shard_id
"""

import asyncio
import os
import logging
from typing import Any
from rustcord import Client, Intents

# Set up logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ShardedBot')

# Configuration
SHARD_COUNT = 2  # Number of shards to use
BOT_TOKEN = os.environ.get('DISCORD_TOKEN')

# Store shard clients
shard_clients: list[Client] = []
guild_counts: list[int] = [0 for _ in range(SHARD_COUNT)]
guild_lists: list[list[str]] = [[] for _ in range(SHARD_COUNT)]


async def on_ready(data: dict[str, Any], shard_id: int):
    """Called when a shard is ready"""
    logger.info(f'Shard {shard_id}/{SHARD_COUNT} is ready!')

    # Get user info
    me = await shard_clients[shard_id].get_current_user()
    if me:
        logger.info(
            f'Logged in as {me.username}#{me.discriminator} on shard {shard_id}'
        )
    else:
        logger.info(f'Logged in on shard {shard_id} (could not get user details)')

    # Get guilds for this shard
    guilds = await shard_clients[shard_id].get_current_guilds()
    guild_counts[shard_id] = len(guilds)

    # Create a list of guild names with IDs
    guild_names = []
    for guild in guilds:
        guild_name = getattr(guild, 'name', 'Unknown')
        guild_id = getattr(guild, 'id', 'Unknown')
        guild_names.append(f'{guild_name} (ID: {guild_id})')

    guild_lists[shard_id] = guild_names

    logger.info(f'Shard {shard_id} is connected to {len(guilds)} guilds')

    # Check if all shards are ready
    if all(count > 0 for count in guild_counts):
        total_guilds = sum(guild_counts)
        logger.info(
            f'All shards are ready! Connected to {total_guilds} guilds in total'
        )

        # Print guild distribution
        for i in range(SHARD_COUNT):
            logger.info(
                f'Shard {i} handles {guild_counts[i]} guilds ({guild_counts[i]/total_guilds*100:.1f}%)'
            )
            for guild in guild_lists[i][
                :5
            ]:  # Only show first 5 guilds per shard to avoid spam
                logger.info(f'  - {guild}')
            if len(guild_lists[i]) > 5:
                logger.info(f'  - ... and {len(guild_lists[i]) - 5} more')


async def on_message(data: dict[str, Any], shard_id: int):
    """Called when a message is received on any shard"""
    content = data.get('content', '')
    author = data.get('author', {})
    channel_id = data.get('channel_id', '')

    # Don't respond to our own messages
    current_user = await shard_clients[shard_id].get_current_user()
    if current_user and author.get('id') == current_user.id:
        return

    # Simple command handler
    if content == '!shardinfo':
        await shard_clients[shard_id].send_message(
            channel_id,
            f"I'm running on shard {shard_id} of {SHARD_COUNT}.\n"
            f'This shard is connected to {guild_counts[shard_id]} guilds.\n'
            f'All shards together are connected to {sum(guild_counts)} guilds.',
        )


async def start_shard(shard_id: int):
    """Start a single shard"""
    # Create Discord client with sharding configuration
    client = Client(
        token=BOT_TOKEN,
        intents=Intents.DEFAULT,
        shard_id=shard_id,
        shard_count=SHARD_COUNT,
    )

    # Store the client in our list
    shard_clients.append(client)

    # Register event handlers with shard_id context
    @client.event('ready')
    async def _on_ready(data):
        await on_ready(data, shard_id)

    @client.event('message')
    async def _on_message(data):
        await on_message(data, shard_id)

    # Connect to Discord
    try:
        logger.info(f'Starting shard {shard_id}/{SHARD_COUNT}...')
        await client.start()
    except Exception as e:
        logger.error(f'Error in shard {shard_id}: {e}')


async def main():
    """Main function to run all shards"""
    # Start all shards
    shard_tasks = []
    for shard_id in range(SHARD_COUNT):
        # Discord requires a 5-second delay between shard startups
        if shard_id > 0:
            logger.info(f'Waiting 5 seconds before starting shard {shard_id}...')
            await asyncio.sleep(5)

        # Start this shard
        task = asyncio.create_task(start_shard(shard_id))
        shard_tasks.append(task)

    # Wait for all shards to connect
    try:
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info('Bot is shutting down...')
        for i, client in enumerate(shard_clients):
            logger.info(f'Disconnecting shard {i}...')
            await client.disconnect()


if __name__ == '__main__':
    if not BOT_TOKEN:
        logger.error('Please set the DISCORD_TOKEN environment variable')
        exit(1)

    # Run the bot
    asyncio.run(main())
