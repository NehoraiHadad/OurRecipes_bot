import logging
import os
from telegram.ext import (ApplicationBuilder, CallbackQueryHandler)

from handlers import(
    edit_conv_handler,
    search_conv_handler,
    add_conv_handler,
    more_details_handler,
    share_start_handler,
    share_public_state_handler,
    share_public_togglt_handler,
    share_permission_level_handler,
    share_link_handler,
    share_revoke_user_shared_handler, start_handler,
    inline_query_handler,
    unknown_handler,
)
from modules.helpers.cancel import cancel
from modules.recipes.edit import edit_recipe_callback


api_token = os.environ.get('TELEGRAM_API_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG 
)

# text
txt_edit_recipe = "עריכת מתכון"
txt_cancel = 'בטל 🛑'



def main():

    application = ApplicationBuilder().token(api_token).build()
    
    # commands 
    application.add_handler(start_handler)
    application.add_handler(search_conv_handler)
    application.add_handler(inline_query_handler)
    application.add_handler(unknown_handler)

    # chat buttons
    application.add_handler(add_conv_handler)
    application.add_handler(search_conv_handler)
    application.add_handler(edit_conv_handler)
    application.add_handler(more_details_handler)

    application.add_handler(share_start_handler)
    application.add_handler(share_public_state_handler)
    application.add_handler(share_public_togglt_handler)
    application.add_handler(share_permission_level_handler)
    application.add_handler(share_link_handler)
    application.add_handler(share_revoke_user_shared_handler)

    application.add_handler(CallbackQueryHandler(edit_recipe_callback, pattern=txt_edit_recipe))
    application.add_handler(CallbackQueryHandler(cancel, pattern=txt_cancel))

    
    application.run_polling()

if __name__ == '__main__':
    main()