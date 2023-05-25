from telegram.ext import (CommandHandler, InlineQueryHandler, MessageHandler, filters)
from models import (start, inline_query, unknown)

start_handler = CommandHandler('start', start)
inline_query_handler = InlineQueryHandler(inline_query)
unknown_handler = MessageHandler(filters.COMMAND, unknown)