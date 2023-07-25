
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.helpers import escape_markdown


from modules.dynamoDB import RecipeHandler, UserHandler


user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")

async def inline_query(update, context):
    user_query = update.inline_query.query
    user_id = str(update.effective_user.id)

    # Retrieve matching recipes from database
    owned_recipes = await user_handler.fetch_owned_recipes(user_id)

    matching_recipes_owned = await recipe_handler.search_recipes_by_name(
        owned_recipes, user_query
    )

    results = []
    if matching_recipes_owned: 
        
        for recipe in matching_recipes_owned:
            
            if type(recipe["ingredients"]) != list:
                    recipe["ingredients"] = [
                        ingredient.strip() for ingredient in recipe["ingredients"].split(",")
                    ]

            formatted_ingredients = "\n".join(
                [
                    f"{index+1}.  {ingredient}"
                    for index, ingredient in enumerate(recipe["ingredients"])
                ]
            )

            recipe_str = f'*שם:*  {escape_markdown(recipe["recipe_name"], 2)}\n\n*רכיבים:*  {escape_markdown(formatted_ingredients, 2)}\n\n*הוראות:*  {escape_markdown(recipe["instructions"],2 )}'

            result = InlineQueryResultArticle(
                id=recipe["recipe_id"],
                title=recipe["recipe_name"],
                input_message_content=InputTextMessageContent(
                    message_text=recipe_str, parse_mode="MarkdownV2"
                ),
                thumb_url="https://picsum.photos/200/300",
            )
            results.append(result)

    return await context.bot.answer_inline_query(update.inline_query.id, results)
