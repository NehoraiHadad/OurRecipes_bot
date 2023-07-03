import boto3
from boto3.dynamodb.conditions import Key
from typing import Any, Dict, List, Optional, Set
import datetime

region_name = "us-east-1"

dynamodb_client = boto3.client("dynamodb", region_name=region_name)


class DynamoDBHandler:
    def __init__(self, table_name: str):
        self.dynamodb_client = boto3.resource("dynamodb")
        self.table = self.dynamodb_client.Table(table_name)


class UserHandler(DynamoDBHandler):
    def register_user(
        self, user_id: str, username: str, shared_recipes: Optional[str]
    ) -> Dict[str, Any]:
        existing_user = self.table.get_item(Key={"user_id": user_id})
        current_date = datetime.datetime.now()
        date_format = "%Y-%m-%d %H:%M:%S"
        date_string = current_date.strftime(date_format)

        if existing_user and "Item" in existing_user:
            existing_user = existing_user["Item"]
            existing_user["username"] = username
            if shared_recipes:
                existing_user["shared_recipes"] = existing_user.get(
                    "shared_recipes", set()
                )
                existing_user["shared_recipes"].add(shared_recipes)
            existing_user["last_seen"] = date_string
            response = self.table.put_item(Item=existing_user)
            return response

        else:
            item = {
                "user_id": user_id,
                "username": username,
                "join_in": date_string,
            }
            if shared_recipes:
                item["shared_recipes"] = set()
                item["shared_recipes"].add(shared_recipes)

            response = self.table.put_item(Item=item)

            return response

    def add_owned_recipe(self, user_id: str, recipe_id: str) -> Dict[str, Any]:
        response = self.table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="ADD owned_recipes :recipe",
            ExpressionAttributeValues={":recipe": {recipe_id}},
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]

    def fetch_owned_recipes(self, user_id: str) -> set[str]:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item", {})
        owned_recipes = item.get("owned_recipes", set())

        return owned_recipes

    def fetch_shared_recipes(self, user_id: str) -> set[str]:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item", {})
        shared_recipes = item.get("shared_recipes", set())

        return shared_recipes

    def remove_owned_recipe(self, user_id: str, recipe_id: str):
        key = {"user_id": user_id}
        update_expression = "DELETE owned_recipes :owned_recipes"
        expression_attribute_values = {":owned_recipes": {recipe_id}}
        return self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )


class RecipeHandler(DynamoDBHandler):
    def add_recipe(
        self,
        recipe_id: str,
        user_id: str,
        recipe_name: str,
        ingredients: str,
        instructions: str,
        photo: str,
        recipe_created: str,
        recipe_modified: str,
    ) -> Dict[str, Any]:
        recipe_ingredients_list = [
            ingredient.strip() for ingredient in ingredients.split(",")
        ]
        item = {
            "recipe_id": recipe_id,
            "created_by": user_id,
            "recipe_name": recipe_name,
            "ingredients": recipe_ingredients_list,
            "instructions": instructions,
            "photo_url": photo,
            "recipe_created": recipe_created,
            "recipe_modified": recipe_modified,
        }

        user_handler = UserHandler("users")
        user_handler.add_owned_recipe(user_id, recipe_id)

        response = self.table.put_item(Item=item)

        return response

    def remove_recipe(self, recipe_id: str, user_id: str) -> Dict[str, Any]:
        user_handler = UserHandler("users")
        user_handler.remove_owned_recipe(user_id, recipe_id)

        return self.table.delete_item(Key={"recipe_id": recipe_id})

    def update_recipe(
        self, recipe_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        key = {"recipe_id": recipe_id}
        update_expression = "SET " + ", ".join(
            [f"{key} = :{key}" for key in update_data.keys()]
        )
        expression_attribute_values = {
            f":{key}": value for key, value in update_data.items()
        }
        return self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )

    def search_recipes_by_name(
        self, recipe_ids: List[str], search_query: str
    ) -> List[Dict[str, Any]]:
        matching_recipes = []

        for recipe_id in recipe_ids:
            response = self.table.query(
                KeyConditionExpression="recipe_id = :recipe_id",
                FilterExpression="contains(recipe_name, :query)",
                ExpressionAttributeValues={
                    ":recipe_id": recipe_id,
                    ":query": search_query,
                },
            )
            if response["Items"]:
                matching_recipes.append(response["Items"][0])
        return matching_recipes

    def make_public(self, recipe_id: str) -> None:
        self.table.update_item(
            Key={"recipe_id": recipe_id},
            UpdateExpression="set is_public = :t",
            ExpressionAttributeValues={":t": True},
        )

    def make_all_public(self, user_id: str) -> None:
        User_handler = UserHandler("users")
        user_recipes = User_handler.fetch_owned_recipes(user_id)
        for recipe in user_recipes:
            self.make_public(recipe)

    def fetch_public_recipes(self) -> List[Dict[str, Any]]:
        response = self.table.scan()
        public_recipes = [
            item for item in response["Items"] if item.get("is_public", False)
        ]

        return public_recipes


class SharesHandler(DynamoDBHandler):
    def save_share_info(
        self,
        unique_id: str,
        user_id: str,
        permission_level: str,
        all_recipes: bool = False,
        recipe_id: Optional[str] = None,
    ) -> None:
        item = {
            "unique_id": unique_id,
            "user_id": user_id,
            "permission_level": permission_level,
            "all_recipes": all_recipes,
            "recipe_id": "",
        }

        if not all_recipes:
            assert (
                recipe_id is not None
            ), "Recipe id must be provided when all_recipes is False"
            item["recipe_id"] = recipe_id

        self.table.put_item(Item=item)

    def fetch_share_info(self, unique_id: str) -> Optional[Dict[str, Any]]:
        item = self.table.get_item(Key={"unique_id": unique_id})
        return item if item else None

    def add_share_access(self, unique_id: str, user_id: str):
        key = {"unique_id": unique_id}

        update_expression = "ADD user_id_shared :u"
        expression_attribute_values = {":u": {user_id}}
        self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )

    def revoke_share_access(self, unique_id: str):
        self.table.update_item(
            Key={"unique_id": unique_id},
            UpdateExpression="SET status = :cancelled",
            ExpressionAttributeValues={":cancelled": "cancelled"},
        )
