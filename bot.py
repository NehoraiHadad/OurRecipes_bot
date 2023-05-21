import os
import logging
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler

api_token = os.environ.get('TELEGRAM_API_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# text
txt_add_recipe = "הוסף מתכון חדש"
txt_search_recipe = "חפש מתכון"

txt_cancel = 'בטל🛑'
txt_try_again = "לנסות שוב?🔄"

txt_edit_recipe = "עריכת מתכון"
txt_edit_name = "שם"
txt_edit_ingredients = "רכיבים"
txt_edit_instructions = "תהליך ההכנה"
txt_delete_recipe = "מחק מתכון⁉"

# buttons
cancel_button = InlineKeyboardButton(txt_cancel, callback_data=txt_cancel)
init_buttons = [[InlineKeyboardButton(txt_add_recipe, callback_data=txt_add_recipe)], 
                [InlineKeyboardButton(txt_search_recipe, callback_data=txt_search_recipe)]]
def edit_buttons(recipe_ID):
    return [InlineKeyboardButton(txt_edit_name, callback_data=f'{txt_edit_name}{recipe_ID}'), 
                InlineKeyboardButton(txt_edit_ingredients, callback_data=f'{txt_edit_ingredients}{recipe_ID}'), 
                InlineKeyboardButton(txt_edit_instructions, callback_data=f'{txt_edit_instructions}{recipe_ID}')], [InlineKeyboardButton(txt_delete_recipe, callback_data=txt_delete_recipe)],[cancel_button]

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

    recipe_str = f'שם: {recipe["name"]}\n\nרכיבים: {recipe["ingredients"]}\n\nתהליך ההכנה: {recipe["instructions"]}'
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
        reply_markup=reply_markup
    )

async def txt_display_recipe(update, context, recipe_ID, recipe_str):
    reply_markup = InlineKeyboardMarkup([[edit_recipe_button(recipe_ID)]])
    await update.message.reply_text(f'המתכון שלך:\n\n{recipe_str}', reply_markup=reply_markup)

# add recipe
RECIPE_NAME, RECIPE_INGREDIENTS, RECIPE_INSTRUCTIONS, RECIPE_PHOTO = range(4)
USER_QUERY = 1

async def add_recipe_callback(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text('שם המתכון:', reply_markup=InlineKeyboardMarkup([[cancel_button]]))
    return RECIPE_NAME

async def get_recipe_name(update, context):
    recipe_name = update.message.text
    context.user_data['recipe_name'] = recipe_name
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
    await update.message.reply_text('תהליך ההכנה והערות:', reply_markup=InlineKeyboardMarkup([[cancel_button]]))
    return RECIPE_INSTRUCTIONS 


async def get_instructions(update, context):
    instructions = update.message.text
    context.user_data['recipe_instructions'] = instructions

    # Build the recipe ID
    recipe = {
        'id': uuid.uuid4(),
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

    await update.message.reply_text('מה עוד?', reply_markup=InlineKeyboardMarkup(init_buttons))
    return ConversationHandler.END

async def cancel(update, context):
    await update.callback_query.message.edit_text('הפעולה בוטלה.')
    await update.callback_query.message.reply_text('מה עוד?', reply_markup=InlineKeyboardMarkup(init_buttons))
    context.user_data.clear()
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

    # TO DO - Perform the search and retrieve matching recipes
    matching_recipes = [{
        'id': "1",
        'name': 'ראשון',
        'ingredients': 'ראשון, ראשון, ראשון, ראשון',
        'instructions': 'ראשון ראשון ראשון ראשון ראשון ראשון ראשון ראשון ',
        'photo': ""
    }, {
        'id': "2",
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
    await query.message.reply_text(text = "אז מה לערוך?", reply_markup = InlineKeyboardMarkup(edit_buttons(recipe_ID)))

async def edit_recipe_name(update, context):
    query = update.callback_query
    query.answer()

    recipe_ID = query.data.replace(txt_edit_name, '')
    await update.callback_query.message.reply_text("מהו השם המעודכן?", reply_markup = InlineKeyboardMarkup([[cancel_button]]))
    new_name = update.callback_query.message.text

    recipe = context.user_data[recipe_ID]
    recipe["name"] = new_name
    # update DB

    await update.callback_query.message.reply_text("השינוי נקלט בהצלחה")
    display_recipe(update, context, recipe)

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

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.add_handler(add_conv_handler)
    application.add_handler(search_conv_handler)
    application.add_handler(CallbackQueryHandler(search_recipe_callback, pattern=txt_try_again))
    application.add_handler(CallbackQueryHandler(edit_recipe_callback, pattern=txt_edit_recipe))
    application.add_handler(CallbackQueryHandler(edit_recipe_name, pattern=txt_edit_name))
    application.add_handler(CallbackQueryHandler(cancel, pattern=txt_cancel))


    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)
    
    application.run_polling()

if __name__ == '__main__':
    main()