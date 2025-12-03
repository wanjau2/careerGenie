#!/usr/bin/env python3
"""Test script to verify the import fix."""

try:
    from config.database import get_database
    print("✓ Import 'get_database' from config.database - SUCCESS")
    
    from models.resume_variation import ResumeVariation
    print("✓ Import ResumeVariation model - SUCCESS")
    
    print("\n✅ All imports successful! The issue is fixed.")
    print("\nNote: If you see errors about missing modules like 'flask_jwt_extended',")
    print("that's a different issue - you need to install dependencies:")
    print("  pip install -r requirements.txt")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)
