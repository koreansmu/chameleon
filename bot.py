from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, MessageHandler, InlineQueryHandler, filters)
import functools
import logging

from config import BOT_TOKEN
from constants import TRANSLATION_CHAT_ID
from handlers import group, game, dev, group_settings, private, stats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, filename="log.log")


async def main():
    # Update for bot with Application instead of Updater and use drop_pending_updates instead of clean
    application = Application.builder().token(BOT_TOKEN).build()

    # bot gets added to group
    application.add_handler(MessageHandler(filters.ChatType.GROUP & (filters.StatusUpdate.CHAT_CREATED | filters.StatusUpdate.NEW_CHAT_MEMBERS), group.greeting))
    
    # deeplinking handler, making sure it can catch updates before the other ones
    application.add_handler(CommandHandler("start", stats.private_stats_command, filters.Regex("stats")))
    
    # a group starts a game
    application.add_handler(CommandHandler("start", functools.partial(group.start, dp=application), filters.ChatType.GROUP))
    
    # Game-related handlers
    application.add_handler(CallbackQueryHandler(group.player_join, pattern="join"))
    application.add_handler(CommandHandler("abort_game", game.abort_game, filters.ChatType.GROUP))
    application.add_handler(MessageHandler(filters.ChatType.GROUP & filters.TEXT & filters.Message, game.message))
    application.add_handler(CallbackQueryHandler(game.secret_word, pattern="word"))
    application.add_handler(CallbackQueryHandler(game.vote, pattern="vote"))
    application.add_handler(CallbackQueryHandler(game.draw, pattern="draw"))
    application.add_handler(MessageHandler(filters.ChatType.GROUP & filters.TEXT, game.guess), 1)
    
    # Next game handler
    application.add_handler(CommandHandler("nextgame", group.nextgame_command, filters.ChatType.GROUP))
    application.add_handler(CommandHandler("start", group.nextgame_start, filters.ChatType.PRIVATE), 2)

    # Group commands
    application.add_handler(CommandHandler("game_rules", group.game_rules))
    application.add_handler(CommandHandler("settings", group_settings.group_setting, filters.ChatType.GROUP))
    application.add_handler(CommandHandler("start", group_settings.start, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("admins_reload", group_settings.admins_reload, filters.ChatType.GROUP))
    
    # Group settings
    application.add_handler(CallbackQueryHandler(group_settings.refresh, pattern="(?=.*groupsetting)(?=.*refresh)"))
    application.add_handler(CallbackQueryHandler(group_settings.change_language, pattern=r"(?=.*groupsetting)(?=.*language)"))
    application.add_handler(CallbackQueryHandler(group_settings.select_language, pattern=r"grouplanguage"))
    application.add_handler(CallbackQueryHandler(group_settings.change_deck, pattern=r"(?=.*groupsetting)(?=.*deck)"))
    application.add_handler(CallbackQueryHandler(group_settings.select_deck_language, pattern=r"0deck"))
    application.add_handler(CallbackQueryHandler(group_settings.select_deck, pattern=r"1deck"))
    application.add_handler(CallbackQueryHandler(group_settings.fewer, pattern=r"(?=.*groupsetting)(?=.*fewer)"))
    application.add_handler(CallbackQueryHandler(group_settings.more, pattern=r"(?=.*groupsetting)(?=.*more)"))
    application.add_handler(CallbackQueryHandler(group_settings.tournament, pattern=r"(?=.*groupsetting)(?=.*tournament)"))
    application.add_handler(CallbackQueryHandler(group_settings.pin, pattern=r"(?=.*groupsetting)(?=.*pin)"))
    application.add_handler(CallbackQueryHandler(group_settings.restrict, pattern=r"(?=.*groupsetting)(?=.*restrict)"))
    application.add_handler(CallbackQueryHandler(group_settings.exclamation, pattern=r"(?=.*groupsetting)(?=.*exclamation)"))
    
    # Group changes
    application.add_handler(MessageHandler(filters.StatusUpdate.MIGRATE, group.change_id))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_TITLE, group.change_title))

    # Private language change
    application.add_handler(CommandHandler("language", private.change_language, filters.ChatType.PRIVATE))
    application.add_handler(CallbackQueryHandler(private.selected_language, pattern="privatelanguage"))

    # More private commands
    application.add_handler(CommandHandler("translation", private.translation, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("deck", private.deck, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("start", private.start, filters.ChatType.PRIVATE), 1)
    application.add_handler(CommandHandler("settings_help", private.settings_help, filters.ChatType.PRIVATE))
    application.add_handler(CallbackQueryHandler(private.settings_help_edit, pattern="settingshelp"))
    
    # Stats
    application.add_handler(InlineQueryHandler(stats.private_stats))
    application.add_handler(CommandHandler("stats", stats.private_stats_command, filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("stats", stats.group_stats, filters.ChatType.GROUP))
    
    # Dev tools
    application.add_handler(CommandHandler("id", dev.reply_id))
    application.add_handler(CommandHandler("shutdown", functools.partial(dev.shutdown, application=application), filters.User(208589966)))
    application.add_handler(CommandHandler("upload", dev.upload, filters.Chat(TRANSLATION_CHAT_ID)))
    
    # Help commands
    application.add_handler(CommandHandler("help", group.help_message, filters.ChatType.GROUP))
    application.add_handler(CommandHandler("help", private.help_message, filters.ChatType.PRIVATE))

    # Error handler
    application.add_error_handler(dev.error_handler)

    # Start polling
    await application.start_polling(drop_pending_updates=True)
    
    # Scheduled job
    application.job_queue.run_repeating(stats.reload_sorted_players, 60*60*24, name="reload_sorted", first=0)
    
    # Run the bot
    await application.idle()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())