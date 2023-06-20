import os
import logging
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler)
from commands import (
    start_handler,
    inline_query_handler,
    unknown_handler
)

from handlers import(
    edit_conv_handler,
    search_conv_handler,
    add_conv_handler,
    more_details_handler
)

from models import (
    cancel,
    search_recipe_callback,
    edit_recipe_callback
)

# api_token = os.environ.get('TELEGRAM_API_TOKEN')
api_token = '6144759204:AAEMghm6YQgjZTHQnWJPhz-NmkA5_rcEVcU'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# text
txt_try_again = "לנסות שוב?🔄"
txt_edit_recipe = "עריכת מתכון"
txt_cancel = 'בטל🛑'
txt_more_details = "פרטים נוספים"



def main():

    application = ApplicationBuilder().token(api_token).build()
    
    # commands 
    application.add_handler(start_handler)
    application.add_handler(inline_query_handler)
    application.add_handler(unknown_handler)

    # chat buttons
    application.add_handler(add_conv_handler)
    application.add_handler(search_conv_handler)
    application.add_handler(edit_conv_handler)
    application.add_handler(more_details_handler)
    application.add_handler(CallbackQueryHandler(search_recipe_callback, pattern=txt_try_again))
    application.add_handler(CallbackQueryHandler(edit_recipe_callback, pattern=txt_edit_recipe))
    application.add_handler(CallbackQueryHandler(cancel, pattern=txt_cancel))

    
    application.run_polling()

if __name__ == '__main__':
    main()