import boto3
from io import BytesIO

# Настройка клиента для MinIO
s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)

bucket_name = 'otus'

# 1. Загрузка файла в бакет
def upload_file():
    file_content = b'This is a test file content'
    file_obj = BytesIO(file_content)

    s3.upload_fileobj(
        file_obj,
        bucket_name,
        'test_file.txt'
    )
    print("File uploaded successfully")

# 2. Получение списка файлов в бакете
def list_files():
    response = s3.list_objects_v2(Bucket=bucket_name)
    if 'Contents' in response:
        print("Files in bucket:")
        for obj in response['Contents']:
            print(f"- {obj['Key']} (size: {obj['Size']} bytes)")
    else:
        print("Bucket is empty")

# 3. Чтение файла из бакета и вывод содержимого
def read_file():
    try:
        response = s3.get_object(Bucket=bucket_name, Key='test_file.txt')
        content = response['Body'].read().decode('utf-8')
        print("\nFile content:")
        print(content)
    except s3.exceptions.NoSuchKey:
        print("File not found in bucket")

if __name__ == "__main__":
    # Выполняем операции
    upload_file()
    list_files()
    read_file()
