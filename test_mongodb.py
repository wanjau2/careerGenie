#!/usr/bin/env python3
"""Test MongoDB connection."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# Load environment variables
load_dotenv()

def test_connection():
    """Test MongoDB connection and permissions."""
    connection_string = os.getenv('MONGODB_URI')
    db_name = os.getenv('DB_NAME', 'career_genie')

    print(f"Testing MongoDB connection...")
    print(f"Database: {db_name}")
    print(f"Connection string: {connection_string[:20]}...{connection_string[-20:]}")
    print()

    try:
        # Create client
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000
        )

        # Test connection
        print("1. Testing connection...")
        client.admin.command('ping')
        print("   ✓ Connection successful!")
        print()

        # Get database
        print("2. Accessing database...")
        db = client[db_name]
        print(f"   ✓ Database '{db_name}' accessible")
        print()

        # List collections
        print("3. Listing collections...")
        collections = db.list_collection_names()
        if collections:
            print(f"   ✓ Found {len(collections)} collections:")
            for coll in collections[:10]:  # Show first 10
                print(f"     - {coll}")
            if len(collections) > 10:
                print(f"     ... and {len(collections) - 10} more")
        else:
            print("   ⚠️  No collections found (this is normal for a new database)")
        print()

        # Test write permission
        print("4. Testing write permissions...")
        test_collection = db['_test_connection']
        result = test_collection.insert_one({'test': True})
        print(f"   ✓ Write successful (ID: {result.inserted_id})")

        # Clean up test document
        test_collection.delete_one({'_id': result.inserted_id})
        print("   ✓ Cleanup successful")
        print()

        print("=" * 60)
        print("✓ All tests passed! MongoDB is configured correctly.")
        print("=" * 60)

        client.close()
        return True

    except OperationFailure as e:
        print(f"✗ Authentication failed: {e}")
        print()
        print("Possible solutions:")
        print("1. Check if username and password are correct")
        print("2. Verify the user has read/write permissions on the database")
        print("3. Check if IP address is whitelisted in MongoDB Atlas")
        print("4. Ensure the database name in the connection string is correct")
        return False

    except ConnectionFailure as e:
        print(f"✗ Connection failed: {e}")
        print()
        print("Possible solutions:")
        print("1. Check if MongoDB Atlas cluster is running")
        print("2. Verify network connectivity")
        print("3. Check if IP address is whitelisted")
        return False

    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False


if __name__ == '__main__':
    test_connection()
