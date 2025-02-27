import boto3
from botocore.exceptions import ClientError
import bcrypt
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
from decimal import Decimal
import face_recognition
import numpy as np
load_dotenv()

def connect_to_dynamodb():
    try:
        dynamodb = boto3.resource('dynamodb',
            region_name=os.getenv('AWS_DEFAULT_REGION'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        )
        print("Successfully connected")
        return dynamodb
    except ClientError as e:
        print(f"Erreur lors de la connexion à DynamoDB: {e}")
        return None

def create_users_table(db):
    table_name = "Users"
    try:
        existing_table = db.Table(table_name)
        existing_table.load()
        print(f"Table {table_name} already exists")
        return existing_table
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            try:
                table = db.create_table(
                    TableName=table_name,
                    KeySchema=[
                        {'AttributeName': 'email', 'KeyType': 'HASH'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'email', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                print(f"Table {table_name} en cours de création...")
                table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
                print(f"Table {table_name} created successfully")
                return table
            except ClientError as e:
                print(f"Error creating table: {e}")
                return None
        else:
            print(f"Error checking table existence: {e}")
            return None
def save_face_encoding(table, email, face_encoding):
    try:
        print(f"Attempting to save face encoding for {email}")
        
        # Convertir le numpy array en liste de Decimal
        face_encoding_list = [Decimal(str(x)) for x in face_encoding.tolist()]
        
        table.update_item(
            Key={'email': email},
            UpdateExpression='SET face_encoding = :enc',
            ExpressionAttributeValues={
                ':enc': face_encoding_list
            }
        )
        print("Face encoding saved successfully")
        return True
    except Exception as e:
        print(f"Error saving face encoding: {e}")
        return False

# Il faut aussi modifier la fonction verify_face pour reconvertir les Decimal en float
def verify_face(table, email, face_encoding_to_verify):
    try:
        response = table.get_item(Key={'email': email})
        if 'Item' not in response or 'face_encoding' not in response['Item']:
            print("No face encoding found for this user")
            return False
            
        # Convertir les Decimal en float pour la comparaison
        stored_encoding = np.array([float(x) for x in response['Item']['face_encoding']])
        result = face_recognition.compare_faces([stored_encoding], face_encoding_to_verify, tolerance=0.2)[0]
        print(f"Face verification result: {result}")
        return result
    except Exception as e:
        print(f"Error verifying face: {e}")
        return False 

def add_user(table, email, password):
    try:
        response = table.get_item(Key={'email': email})
        if 'Item' in response:
            print(f"User with email {email} already exists")
            return False

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        table.put_item(
            Item={
                'email': email,
                'password': hashed_password.decode('utf-8'),
                'jwtToken': None,  
                'created_at': datetime.now().isoformat()
            }
        )
        print(f"User {email} created successfully")
        return True
        
    except ClientError as e:
        print(f"Error adding user: {e}")
        return False

def logout_user(table, email):
    try:
        table.update_item(
            Key={'email': email},
            UpdateExpression='SET jwtToken = :val',
            ExpressionAttributeValues={':val': None}
        )
        return True
    except ClientError as e:
        print(f"Error during logout: {e}")
        return False
    
def login_user(table, email, password=None, face_auth=False):
    try:
        # Récupérer l'utilisateur
        response = table.get_item(Key={'email': email})
        
        # Vérifier si l'utilisateur existe
        if 'Item' not in response:
            print(f"No user found with email {email}")
            return None

        user = response['Item']

        if not face_auth:
            if not password:
                print("Password required for non-face auth")
                return None
                
            stored_password = user['password'].encode('utf-8')
            if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
                print("Invalid password")
                return None

        # Générer le JWT token
        token = generate_jwt_token(email)
        
        # Mettre à jour le token dans la base de données
        table.update_item(
            Key={'email': email},
            UpdateExpression='SET jwtToken = :token',
            ExpressionAttributeValues={':token': token}
        )
        
        return token

    except ClientError as e:
        print(f"Error during login: {e}")
        return None

def generate_jwt_token(email):
    SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY environment variable is not set")
    
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(days=1), 
        'iat': datetime.utcnow()  
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

def main():
    db = connect_to_dynamodb()
    if db is None:
        print("Failed to connect to DynamoDB")
        exit(1)

    users_table = create_users_table(db)
    if users_table is None:
        print("Failed to create/get Users table")
        exit(1)

if __name__ == "__main__":
    main()