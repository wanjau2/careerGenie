"""Test script for Google Forms integration."""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from services.google_forms_service import GoogleFormsService


def test_service_initialization():
    """Test that the Google Forms service initializes correctly."""
    print("=" * 60)
    print("TEST 1: Service Initialization")
    print("=" * 60)

    try:
        service = GoogleFormsService()

        if service.credentials is None:
            print("❌ FAILED: Service credentials not initialized")
            print(f"   Check that GOOGLE_SERVICE_ACCOUNT_FILE exists at: {os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')}")
            return False

        if service.drive_service is None:
            print("❌ FAILED: Drive service not initialized")
            return False

        if service.sheets_service is None:
            print("❌ FAILED: Sheets service not initialized")
            return False

        print("✅ PASSED: All services initialized successfully")
        print(f"   - Credentials: OK")
        print(f"   - Drive Service: OK")
        print(f"   - Sheets Service: OK")
        return True

    except Exception as e:
        print(f"❌ FAILED: Exception during initialization: {str(e)}")
        return False


def test_form_access():
    """Test access to the Google Form spreadsheet."""
    print("\n" + "=" * 60)
    print("TEST 2: Form Access & Permissions")
    print("=" * 60)

    form_id = os.getenv('GOOGLE_FORM_ID')

    if not form_id:
        print("❌ FAILED: GOOGLE_FORM_ID not set in .env")
        return False

    print(f"Form ID: {form_id}")

    try:
        service = GoogleFormsService()

        if not service.sheets_service:
            print("❌ FAILED: Sheets service not available")
            return False

        # Try to access the form responses
        print("\nAttempting to access form responses...")

        # Google Forms creates a linked spreadsheet with responses
        # The form ID is usually the same as the spreadsheet ID
        result = service.sheets_service.spreadsheets().get(
            spreadsheetId=form_id
        ).execute()

        print("✅ PASSED: Successfully accessed the form spreadsheet")
        print(f"   - Title: {result.get('properties', {}).get('title', 'N/A')}")

        # List available sheets
        sheets = result.get('sheets', [])
        print(f"   - Available sheets/tabs:")
        for sheet in sheets:
            sheet_title = sheet['properties']['title']
            print(f"     • {sheet_title}")

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"❌ FAILED: Cannot access form spreadsheet")
        print(f"   Error: {error_msg}")

        if "403" in error_msg or "permission" in error_msg.lower():
            print("\n   ⚠️  PERMISSION ISSUE DETECTED!")
            print("   Please ensure you've shared the form with:")
            print("   careergenie-forms-service-175@career-genie-476008.iam.gserviceaccount.com")
            print("   as an EDITOR")

        return False


def test_read_responses():
    """Test reading form responses."""
    print("\n" + "=" * 60)
    print("TEST 3: Reading Form Responses")
    print("=" * 60)

    form_id = os.getenv('GOOGLE_FORM_ID')

    try:
        service = GoogleFormsService()

        if not service.sheets_service:
            print("❌ FAILED: Sheets service not available")
            return False

        # Try to read form responses (usually in "Form Responses 1" sheet)
        print("Attempting to read form responses...")

        result = service.sheets_service.spreadsheets().values().get(
            spreadsheetId=form_id,
            range='Form Responses 1!A1:Z100'
        ).execute()

        values = result.get('values', [])

        if not values:
            print("⚠️  WARNING: Form has no responses yet")
            print("   This is normal if no one has submitted the form")
            print("   The integration is working correctly!")
            return True

        print("✅ PASSED: Successfully read form responses")
        print(f"   - Total rows (including header): {len(values)}")
        print(f"   - Response count: {len(values) - 1}")

        if len(values) > 0:
            print(f"   - Columns: {', '.join(values[0])}")

        return True

    except Exception as e:
        error_msg = str(e)
        print(f"❌ FAILED: Cannot read form responses")
        print(f"   Error: {error_msg}")

        if "Unable to parse range" in error_msg:
            print("\n   ⚠️  Sheet 'Form Responses 1' not found")
            print("   This sheet is created automatically when someone submits the form")
            print("   Try submitting a test response to the form first")

        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Google Forms Integration Test" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")

    # Check environment variables
    print("\nEnvironment Configuration:")
    print(f"  GOOGLE_SERVICE_ACCOUNT_FILE: {os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')}")
    print(f"  GOOGLE_FORM_ID: {os.getenv('GOOGLE_FORM_ID')}")

    results = []

    # Run tests
    results.append(("Service Initialization", test_service_initialization()))
    results.append(("Form Access", test_form_access()))
    results.append(("Read Responses", test_read_responses()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Google Forms integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")

    print()


if __name__ == "__main__":
    main()
