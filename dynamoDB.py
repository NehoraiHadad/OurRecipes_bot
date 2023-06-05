import boto3
from typing import Any, Dict, List


class DynamoDBHandler:
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)

    def put_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return self.table.put_item(Item=item)

    def scan(self, filter_expression: Any) -> Dict[str, Any]:
        return self.table.scan(FilterExpression=filter_expression)


class UserRegistrationHandler(DynamoDBHandler):
    def register_user(self, user_id: int, username: str, accessibleRecipe: str) -> Dict[str, Any]:
        item = {'user_id': user_id, 'username': username, 'accessible_recipes': accessibleRecipe}
        return self.put_item(item)
    

class RecipeHandler(DynamoDBHandler):
    def add_recipe(self, recipe_id, user_id: int, recipe_name: str, ingredients: str, instructions: str, photo: str) -> Dict[str, Any]:
        item = {'recipe_id': recipe_id, 'user_id': user_id, 'recipe_name': recipe_name, 'ingredients': ingredients, 'instructions': instructions, 'photo': photo}
        return self.put_item(item)

    def get_user_recipes(self, user_id: int) -> List[Dict[str, Any]]:
        filter_expression = boto3.dynamodb.conditions.Attr('user_id').eq(user_id)
        response = self.scan(filter_expression)
        return response['Items']
    
    def remove_recipe(self, recipe_id: str) -> Dict[str, Any]:
        key = {'recipe_id': recipe_id}
        return self.delete_item(key)

    def update_recipe(self, recipe_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        key = {'recipe_id': recipe_id}
        update_expression = "SET " + ", ".join([f"{key} = :{key}" for key in update_data.keys()])
        expression_attribute_values = {f":{key}": value for key, value in update_data.items()}
        return self.update_item(key, update_expression, expression_attribute_values)


# # Example usage
# user_registration_handler = UserRegistrationHandler('users')
# user_registration_handler.register_user(123456, 'john_doe')

# recipe_handler = RecipeHandler('recipes')
# recipe_handler.add_recipe(123456, 'Pasta Carbonara', 'Spaghetti, Eggs, Bacon, Parmesan Cheese', '1. Cook pasta. 2. Fry bacon. 3. Beat eggs...')

# recipes = recipe_handler.get_user_recipes(123456)
# print(recipes)
