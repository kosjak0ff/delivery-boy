from __future__ import annotations

import asyncio
import logging
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from delivery_boy.config import load_config
from delivery_boy.logging_setup import configure_logging
from delivery_boy.services.forwarder import TelegramForwarder
from delivery_boy.services.monitor import ChannelMonitor
from delivery_boy.storage.db import connect, initialize
from delivery_boy.storage.repository import Repository
from delivery_boy.telegram_web.client import TelegramWebClient


async def run() -> None:
    config = load_config()
    configure_logging(config.log_level, config.log_file_path)
    logger = logging.getLogger(__name__)

    logger.info("Starting delivery-boy service.")

    connection = connect(config.database_path)
    initialize(connection)
    repository = Repository(connection)
    telegram_web_client = TelegramWebClient(
        base_url=config.telegram_web_base_url,
        timeout_seconds=config.request_timeout_seconds,
        retries=config.request_retries,
        user_agent=config.user_agent,
    )
    forwarder = TelegramForwarder(
        bot_token=config.bot_token,
        chat_id=config.chat_id,
        message_thread_id=config.message_thread_id,
        max_message_length=config.max_message_length,
    )
    await forwarder.initialize()
    monitor = ChannelMonitor(
        channels=config.channels,
        repository=repository,
        telegram_web_client=telegram_web_client,
        forwarder=forwarder,
        max_posts_per_channel=config.max_posts_per_channel,
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        monitor.run_once,
        trigger="interval",
        seconds=config.poll_interval_seconds,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for signame in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(signame, stop_event.set)

    try:
        await monitor.run_once()
        await stop_event.wait()
    finally:
        logger.info("Shutting down delivery-boy service.")
        scheduler.shutdown(wait=False)
        await telegram_web_client.close()
        await forwarder.close()
        connection.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
