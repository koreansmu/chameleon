from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, InlineQueryHandler, filters
import functools
import logging

from config import BOT_TOKEN
from constants import TRANSLATION_CHAT_ID
from handlers import group, game, dev, group_settings, private, stats

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, filename="log.log")


def main():
    # Since we are facing timeout error, I will keep increasing those until they are done
    updater = Updater(token=BOT_TOKEN, use_context=True,
                      request_kwargs={'read_timeout': 10, 'connect_timeout': 10})
    dp = updater.dispatcher

    # bot gets added to group
    dp.add_handler(MessageHandler(filters.ChatType.GROUP & (filters.StatusUpdate.chat_created | filters.StatusUpdate.new_chat_members),
                                  group.greeting))
    
    # Deeplinking handler
    dp.add_handler(CommandHandler("start", stats.private_stats_command, filters=filters.Regex("stats")))

    # Game-related handlers
    dp.add_handler(CommandHandler("start", functools.partial(group.start, dp=dp), filters=filters.chat_type.group))
    dp.add_handler(CallbackQueryHandler(group.player_join, pattern="join"))
    dp.add_handler(CommandHandler("abort_game", game.abort_game, filters=filters.chat_type.group))
    dp.add_handler(MessageHandler(filters.chat_type.group & filters.text & filters.update.message, game.message))
    dp.add_handler(CallbackQueryHandler(game.secret_word, pattern="word"))
    dp.add_handler(CallbackQueryHandler(game.vote, pattern="vote"))
    dp.add_handler(CallbackQueryHandler(game.draw, pattern="draw"))
    dp.add_handler(MessageHandler(filters.chat_type.group & filters.text, game.guess), 1)

    # Next game handler
    dp.add_handler(CommandHandler("nextgame", group.nextgame_command, filters=filters.chat_type.group))
    dp.add_handler(CommandHandler("start", group.nextgame_start, filters=filters.chat_type.private), 2)

    # Group-related commands
    dp.add_handler(CommandHandler("game_rules", group.game_rules))
    dp.add_handler(CommandHandler("settings", group_settings.group_setting, filters=filters.chat_type.group))
    dp.add_handler(CommandHandler("start", group_settings.start, filters=filters.chat_type.private))
    dp.add_handler(CommandHandler("admins_reload", group_settings.admins_reload, filters=filters.chat_type.group))
    
    # Group settings
    dp.add_handler(CallbackQueryHandler(group_settings.refresh, pattern="(?=.*groupsetting)(?=.*refresh)"))
    dp.add_handler(CallbackQueryHandler(group_settings.change_language, pattern=r"(?=.*groupsetting)(?=.*language)"))
    dp.add_handler(CallbackQueryHandler(group_settings.select_language, pattern=r"grouplanguage"))
    dp.add_handler(CallbackQueryHandler(group_settings.change_deck, pattern=r"(?=.*groupsetting)(?=.*deck)"))
    dp.add_handler(CallbackQueryHandler(group_settings.select_deck_language, pattern=r"0deck"))
    dp.add_handler(CallbackQueryHandler(group_settings.select_deck, pattern=r"1deck"))
    dp.add_handler(CallbackQueryHandler(group_settings.fewer, pattern=r"(?=.*groupsetting)(?=.*fewer)"))
    dp.add_handler(CallbackQueryHandler(group_settings.more, pattern=r"(?=.*groupsetting)(?=.*more)"))
    dp.add_handler(CallbackQueryHandler(group_settings.tournament, pattern=r"(?=.*groupsetting)(?=.*tournament)"))
    dp.add_handler(CallbackQueryHandler(group_settings.pin, pattern=r"(?=.*groupsetting)(?=.*pin)"))
    dp.add_handler(CallbackQueryHandler(group_settings.restrict, pattern=r"(?=.*groupsetting)(?=.*restrict)"))
    dp.add_handler(CallbackQueryHandler(group_settings.exclamation, pattern=r"(?=.*groupsetting)(?=.*exclamation)"))

    # Group changes
    dp.add_handler(MessageHandler(filters.StatusUpdate.migrate, group.change_id))
    dp.add_handler(MessageHandler(filters.StatusUpdate.new_chat_title, group.change_title))

    # Private language change
    dp.add_handler(CommandHandler("language", private.change_language, filters=filters.chat_type.private))
    dp.add_handler(CallbackQueryHandler(private.selected_language, pattern="privatelanguage"))

    # More private commands
    dp.add_handler(CommandHandler("translation", private.translation, filters=filters.chat_type.private))
    dp.add_handler(CommandHandler("deck", private.deck, filters=filters.chat_type.private))
    dp.add_handler(CommandHandler("start", private.start, filters=filters.chat_type.private), 1)
    dp.add_handler(CommandHandler("settings_help", private.settings_help, filters=filters.chat_type.private))
    dp.add_handler(CallbackQueryHandler(private.settings_help_edit, pattern="settingshelp"))

    # Stats
    dp.add_handler(InlineQueryHandler(stats.private_stats))
    dp.add_handler(CommandHandler("stats", stats.private_stats_command, filters=filters.chat_type.private))
    dp.add_handler(CommandHandler("stats", stats.group_stats, filters=filters.chat_type.group))

    # Dev tools
    dp.add_handler(CommandHandler("id", dev.reply_id))
    dp.add_handler(CommandHandler("shutdown", functools.partial(dev.shutdown, updater=updater), filters=filters.user(208589966)))
    dp.add_handler(CommandHandler("upload", dev.upload, filters=filters.chat(TRANSLATION_CHAT_ID)))

    # Help commands
    dp.add_handler(CommandHandler("help", group.help_message, filters=filters.chat_type.group))
    dp.add_handler(CommandHandler("help", private.help_message, filters=filters.chat_type.private))

    # Error handler
    dp.add_error_handler(dev.error_handler)

    # Start bot
    updater.start_polling(drop_pending_updates=True)
    
    # Scheduled job
    updater.job_queue.run_repeating(stats.reload_sorted_players, 60*60*24, name="reload_sorted", first=0)

    # Run the bot
    updater.idle()


if __name__ == "__main__":
    main()