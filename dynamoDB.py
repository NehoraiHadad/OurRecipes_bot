import boto3
from typing import Any, Dict, List
import datetime

region_name = "us-east-1"

dynamodb_client = boto3.client("dynamodb", region_name=region_name)

class DynamoDBHandler:
    def __init__(self, table_name: str):
        self.dynamodb_client = boto3.resource("dynamodb")
        self.table = self.dynamodb_client.Table(table_name)

    def get_item(self, user_id: int) -> Dict[str, Any]:
        response = self.table.get_item(Key={'user_id': user_id})
        return response.get('Item', {})
    
    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        response = self.table.put_item(Item=item)
        return response

    def scan(self, filter_expression: Any) -> Dict[str, Any]:
        return self.table.scan(FilterExpression=filter_expression)

    def update_item(
        self,
        key: Dict[str, Any],
        update_expression: str,
        expression_attribute_values: Dict[str, Any],
    ) -> Dict[str, Any]:
        response = self.table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
        )
        return response

    def delete_item(self, recipe_id: str) -> Dict[str, Any]:
        response = self.table.delete_item(Key={"recipe_id": recipe_id})
        return response


class UserHandler(DynamoDBHandler):
    def register_user(
        self, user_id: str, username: str, accessibleRecipes: list[str]
    ) -> Dict[str, Any]:
        existing_user = self.table.get_item(Key={"user_id": user_id})
        current_times = datetime.datetime.now().isoformat()

        if existing_user and "Item" in existing_user:
            existing_user = existing_user["Item"]
            # User already exists, update the necessary attributes
            existing_user["username"] = username

            if "accessible_recipes" in existing_user:
                existing_user["accessible_recipes"].extend(accessibleRecipes)
            else:
                existing_user["accessible_recipes"] = accessibleRecipes
            existing_user["last_seen"] = current_times
            response = self.put_item(existing_user)
            return response
        else:
            # User doesn't exist, create a new user item

            item = {
                "user_id": user_id,
                "username": username,
                "accessible_recipes": accessibleRecipes,
                "join_in" : current_times
            }
            response = self.put_item(item)
            return response

    def add_accessible_recipe(self, user_id: str, recipe_id: str) -> Dict[str, Any]:
        response = self.table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET accessible_recipes = list_append(accessible_recipes, :recipe)",
            ExpressionAttributeValues={":recipe": [recipe_id]},
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]

    def get_accessible_recipes(self, user_id: str) -> List[str]:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item", {})
        accessible_recipes = item.get("accessible_recipes", [])

        return accessible_recipes

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

    def get_user_recipes(self, user_id: str) -> List[Dict[str, Any]]:
        filter_expression = boto3.dynamodb_client.conditions.Attr("created_by").eq(
            user_id
        )
        response = self.scan(filter_expression)
        return response["Items"]

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
