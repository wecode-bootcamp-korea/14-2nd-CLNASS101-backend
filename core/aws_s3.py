import uuid 

import boto3

from clnass_101     import settings

class S3FileManager:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

    def file_upload(self, file, file_name):
        self.s3.upload_fileobj(
            file, 
            settings.AWS_STORAGE_BUCKET_NAME, 
            file_name
        )
        return file_name

    def file_delete(self, file_name):
        self.s3.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_name
        )

