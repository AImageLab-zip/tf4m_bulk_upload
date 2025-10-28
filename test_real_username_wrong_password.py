"""
Test login with correct username but wrong password.
This is a critical test case - the server knows the username exists,
but the password is incorrect.
"""

from core.api_client import TF4MAPIClient

def test_correct_username_wrong_password():
    """Test with real username but wrong password."""
    
    base_url = "https://toothfairy4m.ing.unimore.it"
    correct_username = "fbolelli"
    wrong_password = "this_is_definitely_wrong_password_12345"
    
    print("=" * 70)
    print("TEST: Correct Username + Wrong Password")
    print("=" * 70)
    print()
    print(f"Base URL: {base_url}")
    print(f"Username: {correct_username}")
    print(f"Password: {'*' * len(wrong_password)} (WRONG)")
    print()
    
    # Create client
    client = TF4MAPIClient(
        base_url=base_url,
        username=correct_username,
        password=wrong_password
    )
    
    print("Attempting login...")
    success, message = client.login()
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Success: {success}")
    print(f"Message: {message}")
    print(f"Is Authenticated: {client.is_authenticated}")
    print(f"Has sessionid cookie: {'sessionid' in client.session.cookies}")
    print()
    
    if success:
        print("❌ FAIL: Wrong password was accepted! Bug still present.")
        return False
    else:
        print("✅ PASS: Wrong password was correctly rejected!")
        return True

def test_via_test_connection():
    """Test using the test_connection method (used by settings dialog)."""
    
    base_url = "https://toothfairy4m.ing.unimore.it"
    correct_username = "fbolelli"
    wrong_password = "this_is_definitely_wrong_password_12345"
    
    print("\n" + "=" * 70)
    print("TEST: Using test_connection() method (Settings Dialog scenario)")
    print("=" * 70)
    print()
    
    client = TF4MAPIClient(
        base_url=base_url,
        username=correct_username,
        password=wrong_password
    )
    
    print("Calling test_connection()...")
    success, message = client.test_connection()
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Success: {success}")
    print(f"Message: {message}")
    print()
    
    if success:
        print("❌ FAIL: test_connection() succeeded with wrong password!")
        return False
    else:
        print("✅ PASS: test_connection() correctly rejected wrong password!")
        return True

if __name__ == "__main__":
    print("Testing with REAL username 'fbolelli' but WRONG password\n")
    
    result1 = test_correct_username_wrong_password()
    result2 = test_via_test_connection()
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    if result1 and result2:
        print("✅ All tests PASSED! The fix is working correctly.")
        print("   Wrong passwords are properly rejected, even with valid usernames.")
    else:
        print("❌ Some tests FAILED! Bug may still be present.")
