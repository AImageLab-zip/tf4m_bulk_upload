"""
Test the fixed login logic to verify wrong credentials are properly rejected.
"""

from core.api_client import TF4MAPIClient
import sys

def test_wrong_credentials():
    """Test that wrong credentials are properly rejected."""
    
    base_url = "https://toothfairy4m.ing.unimore.it"
    wrong_username = "wrong_user_test_12345"
    wrong_password = "wrong_password_test_12345"
    
    print("=" * 60)
    print("Testing LOGIN with WRONG credentials")
    print("=" * 60)
    
    # Create client with wrong credentials
    client = TF4MAPIClient(
        base_url=base_url,
        username=wrong_username,
        password=wrong_password
    )
    
    # Test connection (which triggers login)
    print(f"\nAttempting login with:")
    print(f"  Username: {wrong_username}")
    print(f"  Password: {'*' * len(wrong_password)}")
    print()
    
    success, message = client.test_connection()
    
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    print()
    
    if success:
        print("❌ BUG STILL PRESENT: Wrong credentials returned success!")
        return False
    else:
        print("✅ CORRECT: Wrong credentials were properly rejected!")
        return True

def test_login_directly():
    """Test the login method directly."""
    
    base_url = "https://toothfairy4m.ing.unimore.it"
    wrong_username = "wrong_user_test_12345"
    wrong_password = "wrong_password_test_12345"
    
    print("\n" + "=" * 60)
    print("Testing DIRECT LOGIN with WRONG credentials")
    print("=" * 60)
    
    client = TF4MAPIClient(
        base_url=base_url,
        username=wrong_username,
        password=wrong_password
    )
    
    print(f"\nAttempting direct login...")
    success, message = client.login()
    
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    print(f"Is Authenticated: {client.is_authenticated}")
    print(f"Has sessionid cookie: {'sessionid' in client.session.cookies}")
    print()
    
    if success:
        print("❌ BUG STILL PRESENT: Wrong credentials returned success!")
        return False
    else:
        print("✅ CORRECT: Wrong credentials were properly rejected!")
        return True

if __name__ == "__main__":
    result1 = test_wrong_credentials()
    result2 = test_login_directly()
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    if result1 and result2:
        print("✅ All tests passed! The bug is fixed.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Bug still present.")
        sys.exit(1)
