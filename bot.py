import os
import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, InlineQueryHandler

api_token = os.environ.get('TELEGRAM_API_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# state for conv handler
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_PHOTO = range(4)
USER_QUERY = 1
GET_NEW_VALUE, GET_DELETE_RECIPE = range(2)

# text
txt_add_recipe = "הוסף מתכון חדש"
txt_search_recipe = "חפש מתכון"

txt_cancel = 'בטל🛑'
txt_try_again = "לנסות שוב?🔄"

txt_edit_recipe = "עריכת מתכון"
txt_edit = "edit"
txt_edit_name = "שם"
txt_edit_ingredients = "רכיבים"
txt_edit_instructions = "הוראות"
txt_edit_photo = "תמונה"
txt_delete_recipe = "מחק מתכון⁉"
txt_delete = "מחק"

# buttons
cancel_button = InlineKeyboardButton(txt_cancel, callback_data=txt_cancel)
init_buttons = [[InlineKeyboardButton(txt_add_recipe, callback_data=txt_add_recipe)], 
                [InlineKeyboardButton(txt_search_recipe, callback_data=txt_search_recipe)]]

async def edit_buttons(recipe_ID):
    return [InlineKeyboardButton(txt_edit_name, callback_data=f'{txt_edit}_{txt_edit_name}_{recipe_ID}'),
             InlineKeyboardButton(txt_edit_ingredients, callback_data=f'{txt_edit}_{txt_edit_ingredients}_{recipe_ID}')], [InlineKeyboardButton(txt_edit_instructions, callback_data=f'{txt_edit}_{txt_edit_instructions}_{recipe_ID}') , 
            InlineKeyboardButton(txt_edit_photo, callback_data=f'{txt_edit}_{txt_edit_photo}_{recipe_ID}')], [InlineKeyboardButton(txt_delete_recipe, callback_data=f'{txt_edit}_{txt_delete}_{recipe_ID}') ,cancel_button]

def edit_recipe_button(recipe_ID):
    return InlineKeyboardButton(txt_edit_recipe, callback_data=f'{txt_edit_recipe}{recipe_ID}')


# commends
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="אני בוט מתכונים! בו ניתן להוסיף לערוך ולחפש את המתכונים בצורה נוחה...", reply_markup=InlineKeyboardMarkup(init_buttons))

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="לא מכיר את הפקודה הזו  ):")

# display functions
async def display_recipe(update, context, recipe):            
    context.user_data[recipe['id']] = recipe

    recipe_str = f'*שם:*  {recipe["name"]}\n\n*רכיבים:*  {recipe["ingredients"]}\n\n*הוראות:*  {recipe["instructions"]}'
    if recipe["photo"] != "":
        await photo_display_recipe(update, context, recipe["photo"], recipe['id'], recipe_str)
    else:
        await txt_display_recipe(update, context, recipe['id'], recipe_str)

async def photo_display_recipe(update, context, photo, recipe_ID, recipe_str):
    reply_markup = InlineKeyboardMarkup([[edit_recipe_button(recipe_ID)]])
    await context.bot.send_photo(
        update.effective_chat.id,
        photo=photo,
        caption=recipe_str,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def txt_display_recipe(update, context, recipe_ID, recipe_str):
    reply_markup = InlineKeyboardMarkup([[edit_recipe_button(recipe_ID)]])
    await update.message.reply_text(f'המתכון שלך:\n\n{recipe_str}', parse_mode='Markdown', reply_markup=reply_markup)

# add recipe

async def add_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('שם המתכון:', reply_markup=InlineKeyboardMarkup([[cancel_button]]))
    return RECIPE_NAME

async def get_recipe_name(update, context):
    name = update.message.text
    context.user_data['recipe_name'] = name
    await update.message.reply_text('יש תמונה?', reply_markup=InlineKeyboardMarkup([[cancel_button]]))
    return RECIPE_PHOTO

async def get_photo(update, context):
    photo = update.message.photo[-1].file_id
    context.user_data['recipe_photo'] = photo
    await update.message.reply_text('הרכיבים (מופרדים בפסיק):', reply_markup=InlineKeyboardMarkup([[cancel_button]]))
    return RECIPE_INGREDIENTS

async def get_ingredients(update, context):
    ingredients = update.message.text
    context.user_data['recipe_ingredients'] = ingredients
    await update.message.reply_text('הוראות:', reply_markup=InlineKeyboardMarkup([[cancel_button]]))
    return RECIPE_INSTRUCTIONS 


async def get_instructions(update, context):
    instructions = update.message.text
    context.user_data['recipe_instructions'] = instructions

    # Build the recipe ID
    recipe_ID = str(uuid.uuid4())
    recipe = {
        'id': recipe_ID,
        'name': context.user_data['recipe_name'],
        'ingredients': context.user_data['recipe_ingredients'],
        'instructions': context.user_data['recipe_instructions'],
        'photo': context.user_data.get('recipe_photo')
    }
    
    # Send the recipe to the user
    await display_recipe(update, context, recipe)


    # TO DO - send to database

    # Clear the conversation data
    context.user_data.clear()
    context.user_data[recipe_ID] = recipe
    await update.message.reply_text('מה עוד?', reply_markup=InlineKeyboardMarkup(init_buttons))
    return ConversationHandler.END

async def cancel(update, context):
    await update.callback_query.edit_message_text('הפעולה בוטלה.')
    await update.callback_query.message.reply_text('מה עוד?', reply_markup=InlineKeyboardMarkup(init_buttons))
    
    # context.user_data.clear()  -- I need to use pop instead clear method
    return ConversationHandler.END

# search recipe
async def search_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('מה לחפש?', reply_markup=InlineKeyboardMarkup([[cancel_button]]))
    return USER_QUERY
    

async def get_user_search(update, context):
    # Implement the search logic here
    user_query = update.message.text
    context.user_data['user_query'] = user_query

    # TO DO - Perform the search and retrieve matching recipes from DB
    matching_recipes = [{
        'id': '1',
        'name': 'ראשון',
        'ingredients': 'ראשון, ראשון, ראשון, ראשון',
        'instructions': 'ראשון ראשון ראשון ראשון ראשון ראשון ראשון ראשון ',
        'photo': ""
    }, {
        'id': '2',
        'name': 'שני',
        'ingredients': 'שני, שני, שני, שני',
        'instructions': 'שני שני שני שני שני שני שני שני ',
        'photo': ""
    }]
    # matching_recipes = None

    # Send the search results to the user
    if matching_recipes:
        for recipe in matching_recipes:
            await display_recipe(update, context, recipe)
    else:
        await update.message.reply_text('לא מצאתי מתכון מתאים 😕', reply_markup=InlineKeyboardMarkup([[cancel_button,InlineKeyboardButton(txt_try_again, callback_data=txt_try_again) ]]))

    return ConversationHandler.END

# edit recipe

async def edit_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()

    recipe_ID = query.data.replace(txt_edit_recipe, '')
    await query.message.reply_text(text = "אז מה לערוך?", reply_markup = InlineKeyboardMarkup(await edit_buttons(recipe_ID)))
    message_id = query.message.message_id
    context.user_data['message_id'] = message_id
    
async def edit_recipe(update, context):
    query = update.callback_query
    await query.answer()
    action, recipe_ID = query.data.split('_')[1:]

    context.user_data['recipe_ID'] = recipe_ID
    context.user_data['action'] = action

    if action == txt_edit_photo:
        await query.edit_message_text(f"מחכה לשליחת תמונה חדשה", reply_markup = InlineKeyboardMarkup([[cancel_button]]))
    elif action == txt_edit_ingredients or action == txt_edit_instructions or action == txt_edit_name:
        await query.edit_message_text(f"נא להקליד את העדכון ב{action}:", reply_markup = InlineKeyboardMarkup([[cancel_button]]))
    elif action == txt_delete:
        await query.edit_message_text("בטוח שרוצה למחוק?", reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('כן', callback_data='OK to delete'), InlineKeyboardButton('לא', callback_data=txt_cancel)]]))

        message_id_edit = query.message.message_id
        context.user_data['message_id_edit'] = message_id_edit

        return GET_DELETE_RECIPE

    message_id_edit = query.message.message_id
    context.user_data['message_id_edit'] = message_id_edit
    return GET_NEW_VALUE

async def edit_recipe_get_respond(update, context):

    message_id = context.user_data['message_id']
    message_id_edit = context.user_data['message_id_edit']
    message_id_user = update.message.message_id
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id_edit)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id_user)

    action = context.user_data['action']
    recipe_ID = context.user_data['recipe_ID']
    recipe = context.user_data[recipe_ID]

    if action == txt_edit_name:
        new_name = update.message.text
        recipe["name"] = new_name
    elif action == txt_edit_ingredients:
        new_ingredients = update.message.text
        recipe["ingredients"] = new_ingredients
    elif action == txt_edit_instructions:
        new_instructions = update.message.text
        recipe["instructions"] = new_instructions
    elif action == txt_edit_photo:
        new_photo = update.message.photo[-1].file_id
        recipe["photo"] = new_photo

    #  TO DO - update database

    await update.message.reply_text("השינוי נשמר בהצלחה")

    keys_to_clear = ['action', 'recipe_ID', 'message_id_edit', 'message_id']
    for key in keys_to_clear:
        if key in context.user_data:
            del context.user_data[key]
    
    await display_recipe(update, context, recipe)

    return ConversationHandler.END

async def delete_recipe(update, context):
    query = update.callback_query

    message_id = context.user_data['message_id']
    message_id_edit = context.user_data['message_id_edit']

    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id)
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=message_id_edit)

    # TO DO - update DB
    await query.message.reply_text('המתכון נמחק בהצלחה')
    await query.message.reply_text('מה עוד?', reply_markup=InlineKeyboardMarkup(init_buttons))

    return ConversationHandler.END

# inline mode
async def inline_query(update, context):
    query = update.inline_query.query

    # Perform the recipe search based on the query
    # Retrieve matching recipes from your recipe collection or database
    matching_recipes = [{
        'id': '1',
        'name': 'ראשון',
        'ingredients': 'ראשון, ראשון, ראשון, ראשון, ראשון, ראשון',
        'instructions': 'ראשון ראשון ראשון ראשון ראשון ראשון ראשון ראשון ',
        'photo': "url"
    }, {
        'id': '2',
        'name': 'שני',
        'ingredients': 'שני, שני, שני, שני',
        'instructions': 'שני שני שני שני שני שני שני שני ',
        'photo': ""
    }]

    # Generate the inline query results
    results = []
    for recipe in matching_recipes:
        recipe_str = f'*שם:*  {recipe["name"]}\n\n*רכיבים:*  {recipe["ingredients"]}\n\n*הוראות:*  {recipe["instructions"]}'

        result = InlineQueryResultArticle(
            id=recipe["id"],
            title=recipe["name"],
            input_message_content=InputTextMessageContent(
                message_text=recipe_str,
                parse_mode='Markdown'),
            thumb_url="https://picsum.photos/200/300"
        )
        results.append(result)

    # Send the results back to the user
    await context.bot.answer_inline_query(update.inline_query.id, results)

def main():

    application = ApplicationBuilder().token(api_token).build()
    
    add_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_recipe_callback, pattern=txt_add_recipe)],
        states={
            RECIPE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_recipe_name)],
            RECIPE_INGREDIENTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ingredients)],
            RECIPE_PHOTO: [MessageHandler(filters.PHOTO & ~filters.COMMAND, get_photo)],
            RECIPE_INSTRUCTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_instructions)],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern=txt_cancel)],
        allow_reentry=True
    )

    search_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(search_recipe_callback, pattern=txt_search_recipe)],
        states={
            USER_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_user_search)],
        },
    fallbacks=[CallbackQueryHandler(cancel, pattern=txt_cancel)],
        allow_reentry=True
    )

    edit_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_recipe, pattern=txt_edit)],
        states={
            GET_NEW_VALUE: [MessageHandler(filters.TEXT | filters.PHOTO & ~filters.COMMAND, edit_recipe_get_respond)],
            GET_DELETE_RECIPE: [CallbackQueryHandler(delete_recipe, pattern="OK to delete"), CallbackQueryHandler(cancel, pattern=txt_cancel)]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern=txt_cancel)]
    )


    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.add_handler(add_conv_handler)
    application.add_handler(search_conv_handler)
    application.add_handler(edit_conv_handler)
    application.add_handler(CallbackQueryHandler(search_recipe_callback, pattern=txt_try_again))
    application.add_handler(CallbackQueryHandler(edit_recipe_callback, pattern=txt_edit_recipe))
    application.add_handler(CallbackQueryHandler(cancel, pattern=txt_cancel))

    inline_query_handler = InlineQueryHandler(inline_query)
    application.add_handler(inline_query_handler)

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)
    
    application.run_polling()

if __name__ == '__main__':
    main()