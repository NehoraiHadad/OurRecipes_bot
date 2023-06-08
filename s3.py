import boto3
import io

region_name = "us-east-1"
s3_client = boto3.client('s3', region_name=region_name)

bucket_name = 'our-recipes-bot-bucket'
folder_name = 'users_recipe_photos/'

async def upload_photo_to_s3(photo, recipe_id):
    if photo:
        photo_key = f"{folder_name}{recipe_id}"
        s3_client.upload_fileobj(photo, bucket_name, photo_key)
        return photo_key
    return None


def download_photo_from_s3(photo_key):
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=photo_key)
        photo_data = io.BytesIO(response['Body'].read())
        photo_data.seek(0)
        return photo_data
    except Exception as e:
        print(f"Failed to download photo from S3: {str(e)}")
        return None
    
def delete_photo_from_s3(photo_key):
    response =  s3_client.delete_object(Bucket=bucket_name, Key=photo_key)
    return response