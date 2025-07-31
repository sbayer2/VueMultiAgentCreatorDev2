#!/usr/bin/env python3
"""Reset database - remove all users"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, User

def reset_users():
    """Delete all users from the database"""
    db = SessionLocal()
    try:
        # Count users before deletion
        user_count = db.query(User).count()
        print(f"Found {user_count} users in database")
        
        # Delete all users
        deleted = db.query(User).delete()
        db.commit()
        print(f"Deleted {deleted} users")
        
        # Verify
        remaining = db.query(User).count()
        print(f"Remaining users: {remaining}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_users()