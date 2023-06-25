import boto3
from boto3.dynamodb.conditions import Key
from typing import Any, Dict, List, Optional
import datetime

region_name = "us-east-1"

dynamodb_client = boto3.client("dynamodb", region_name=region_name)


class DynamoDBHandler:
    def __init__(self, table_name: str):
        self.dynamodb_client = boto3.resource("dynamodb")
        self.table = self.dynamodb_client.Table(table_name)

    def get_item(self, user_id: int) -> Optional[Dict[str, Any]]:
        response = self.table.get_item(Key={"user_id": user_id})
        return response["Item"] if "Item" in response else None

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        response = self.table.put_item(Item=item)
        return response["Item"] if "Item" in response else None

    def scan(self, filter_expression) -> List[Dict[str, Any]]:
        response = self.table.scan(FilterExpression=filter_expression)
        return response["Items"]

    def update_item(
        self,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
    ) -> None:
        self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )

    def delete_item(self, key: Dict[str, Any]) -> None:
        return self.table.delete_item(Key=key)


class UserHandler(DynamoDBHandler):
    def register_user(
        self, user_id: str, username: str, shared_recipes: Optional[List[str]]
    ) -> Dict[str, Any]:
        existing_user = self.table.get_item(Key={"user_id": user_id})
        current_date = datetime.datetime.now()
        date_format = "%Y-%m-%d %H:%M:%S"
        date_string = current_date.strftime(date_format)

        if existing_user and "Item" in existing_user:
            existing_user = existing_user["Item"]
            existing_user["username"] = username
            if shared_recipes:
                existing_user["shared_recipes"].extend(shared_recipes)
            existing_user["last_seen"] = date_string
            response = self.put_item(existing_user)
            return response
        else:
            item = {
                "user_id": user_id,
                "username": username,
                "accessible_recipes": [],
                "shared_recipes": shared_recipes,
                "join_in": date_string,
            }
            response = self.put_item(item)

            print(response)

            return response

    def add_accessible_recipe(self, user_id: str, recipe_id: str) -> Dict[str, Any]:
        response = self.table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET accessible_recipes = list_append(accessible_recipes, :recipe)",
            ExpressionAttributeValues={":recipe": [recipe_id]},
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]

    def fetch_owned_recipes(self, user_id: str) -> List[str]:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item", {})
        owned_recipes = item.get("owned_recipes", [])

        return owned_recipes

    def fetch_shared_recipes(self, user_id: str) -> List[str]:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item", {})
        shared_recipes = item.get("shared_recipes", [])

        return shared_recipes

    def remove_accessed_recipe(self, user_id: str, recipe_id: str):
        key = {"user_id": user_id}
        user = self.table.get_item(Key=key)
        user = user["Item"]
        if user:
            accessible_recipes = user.get("accessible_recipes", [])
            if recipe_id in accessible_recipes:
                accessible_recipes.remove(recipe_id)
                user["accessible_recipes"] = accessible_recipes
                update_expression = "SET accessible_recipes = :accessible_recipes"
                expression_attribute_values = {
                    ":accessible_recipes": accessible_recipes
                }
                self.update_item(key, update_expression, expression_attribute_values)


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
        item = {
            "recipe_id": recipe_id,
            "created_by": user_id,
            "recipe_name": recipe_name,
            "ingredients": ingredients,
            "instructions": instructions,
            "photo_url": photo,
            "recipe_created": recipe_created,
            "recipe_modified": recipe_modified,
        }

        user_handler = UserHandler("users")
        user_handler.add_accessible_recipe(user_id, recipe_id)

        response = self.table.put_item(Item=item)

        return response

    def remove_recipe(self, recipe_id: str, user_id: str) -> Dict[str, Any]:
        user_handler = UserHandler("users")
        user_handler.remove_accessed_recipe(user_id, recipe_id)

        return self.delete_item(recipe_id)

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
        return self.update_item(key, update_expression, expression_attribute_values)

    def search_recipes_by_name(
        self, accessible_recipe_ids: List[str], search_query: str
    ) -> List[Dict[str, Any]]:
        matching_recipes = []
        for recipe_id in accessible_recipe_ids:
            response = self.table.query(
                KeyConditionExpression="recipe_id = :recipe_id",
                FilterExpression="contains(recipe_name, :query)",
                ExpressionAttributeValues={
                    ":recipe_id": recipe_id,
                    ":query": search_query,
                },
            )
            matching_recipes.extend(response.get("Items", []))
        return matching_recipes

    def make_public(self, recipe_id: str) -> None:
        self.update_item(
            recipe_id,
            "set is_public = :t",
            {":t": True},
        )

    def make_all_public(self, user_id: str) -> None:
        user_recipes = self.fetch_private_recipes(user_id)
        for recipe in user_recipes:
            self.make_public(recipe["recipe_id"])

    def fetch_public_recipes(self) -> List[Dict[str, Any]]:
        filter_expression = Key('is_public').eq(True)
        return self.scan(filter_expression)


class PermissionsHandler(DynamoDBHandler):
    def save_share_link(
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
        }

        if not all_recipes:
            assert (
                recipe_id is not None
            ), "Recipe id must be provided when all_recipes is False"
            item["recipe_id"] = recipe_id

        self.put_item(self.permissions_table, item)

    def fetch_share_info(self, unique_id: str) -> Optional[Dict[str, Any]]:
        item = self.get_item(self.permissions_table, {"unique_id": unique_id})
        return item if item else None

    def add_share_access(self, user_id_shared: str):
        item = {"user_id_shared": user_id_shared}
        self.put_item(self.permissions_table, item)
