import boto3
from typing import Any, Dict, List, Optional
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
                    "shared_recipes", []
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
                "all_recipes_public": False
            }
            if shared_recipes:
                item["shared_recipes"] = []
                item["shared_recipes"].add(shared_recipes)

            response = self.table.put_item(Item=item)

            return response

    def add_owned_recipe(self, user_id: str, recipe_id: str) -> Dict[str, Any]:
        response = self.table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET owned_recipes = list_append(if_not_exists(owned_recipes, :empty_list), :recipe)",
            ExpressionAttributeValues={
                ":recipe": [recipe_id],
                ":empty_list": [],
            },
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]


    def fetch_owned_recipes(self, user_id: str) -> list[str]:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item", {})
        owned_recipes = item.get("owned_recipes", [])

        return owned_recipes

    def fetch_shared_recipes(self, user_id: str) -> list[str]:
        response = self.table.get_item(Key={"user_id": user_id})
        item = response.get("Item", {})
        shared_recipes = item.get("shared_recipes", [])

        return shared_recipes

    def remove_owned_recipe(self, user_id: str, recipe_id: str):
        response = self.table.get_item(Key={"user_id": user_id})
        owned_recipes = response["Item"]["owned_recipes"]

        if recipe_id in owned_recipes:
            owned_recipes.remove(recipe_id)

        update_response = self.table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET owned_recipes = :owned_recipes",
            ExpressionAttributeValues={":owned_recipes": owned_recipes},
        )

        return update_response

    
    def remove_share_recipe(self, user_id: str, unique_id: str):
        response = self.table.get_item(Key={"user_id": user_id})
        if 'Item' in response:
            shared_recipes = response['Item'].get('shared_recipes', [])
            if unique_id in shared_recipes:
                shared_recipes.remove(unique_id)
                return self.table.update_item(
                    Key={"user_id": user_id},
                    UpdateExpression="SET shared_recipes = :unique_id",
                    ExpressionAttributeValues={":unique_id": unique_id}
                )
            
    def update_all_recipes_public(self, user_id: str, all_recipes_public: bool):
        response = self.table.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET all_recipes_public = :arp",
            ExpressionAttributeValues={":arp": all_recipes_public},
            ReturnValues="ALL_NEW",
        )
        return response["Attributes"]
    
    def is_all_public(self, user_id: str) -> bool:
        response = self.table.get_item(Key={"user_id": user_id})

        if 'Item' in response and 'all_recipes_public' in response['Item']:
            return response['Item']['all_recipes_public']
        
        return False
    
    def is_recipe_public(self, recipe_id: str) -> bool:
        recipe = self.table.get_item(Key={"recipe_id": recipe_id}).get("Item", None)

        if recipe and recipe.get("is_public", False):
            return True
        return False

    def get_user_shares(self, user_id: str) -> List[Dict[str, Any]]:
        user = self.table.get_item(Key={"user_id": user_id})["Item"]
        user_shared_ids = user.get("user_shared_ids", [])
        shares = []
        for unique_id in user_shared_ids:
            share = self.shares_table.get_item(Key={"unique_id": unique_id})["Item"]
            shares.append(share)
        return shares

class RecipeHandler(DynamoDBHandler):
    def get_recipe_by_id(self, recipe_id: str) -> Dict[str, Any]:
        response = self.table.get_item(Key={"recipe_id": recipe_id}) 
        if "Item" in response:
            return response["Item"] 
        else: 
            return None

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

    def revoke_public(self, recipe_id: str) -> None:
        self.table.update_item(
            Key={"recipe_id": recipe_id},
            UpdateExpression="set is_public = :t",
            ExpressionAttributeValues={":t": False},
        )

    def revoke_all_public(self, user_id: str) -> None:
        User_handler = UserHandler("users")
        user_recipes = User_handler.fetch_owned_recipes(user_id)
        for recipe in user_recipes:
            self.revoke_public(recipe)

    def fetch_public_recipes(self) -> List[Dict[str, Any]]:
        response = self.table.scan()
        public_recipes = [
            item for item in response["Items"] if item.get("is_public", False)
        ]

        return public_recipes
    
    def is_recipe_public(self, recipe_id: str) -> bool:
        recipe = self.get_recipe_by_id(recipe_id)
        
        return recipe.get("is_public", False)



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
