from modules.dynamoDB import RecipeHandler, SharesHandler, UserHandler


user_handler = UserHandler("users")
recipe_handler = RecipeHandler("recipes")
shares_handler = SharesHandler("shares")


async def update_accessable_recipes(update, context):
    user_id = str(update.effective_user.id)

    all_public_recipes = await recipe_handler.fetch_public_recipes()
    owned_recipes = await user_handler.fetch_owned_recipes(user_id)
    shared_recipes_info = user_handler.fetch_shared_recipes(user_id)

    shared_recipes = set()
    shared_recipe = {}

    for shared_info in shared_recipes_info:
        shared_info = shares_handler.fetch_share_info(shared_info)
        if shared_info:
            if shared_info["all_recipes"]:
                user_shared_recipes = await user_handler.fetch_owned_recipes(
                    shared_info["user_id"]
                )
                shared_recipes.update(user_shared_recipes)

                for recipe in user_shared_recipes:
                    if (
                        recipe not in shared_recipe
                        or shared_info["permission_level"] == "edit"
                    ):
                        shared_recipe[recipe] = (
                            shared_info["permission_level"],
                            shared_info["username"],
                        )
            else:
                shared_recipes.add(shared_info["recipe_id"])
                if (
                    shared_info["recipe_id"] not in shared_recipe
                    or shared_info["permission_level"] == "edit"
                ):
                    shared_recipe[shared_info["recipe_id"]] = (
                        shared_info["permission_level"],
                        shared_info["username"],
                    )

    context.user_data["shared_recipe"] = shared_recipe

    public_recipes = [
        recipe
        for recipe in all_public_recipes
        if recipe["recipe_id"] not in owned_recipes
        and recipe["recipe_id"] not in shared_recipes
    ]

    return owned_recipes, shared_recipes, public_recipes
