"""
Test that simulates the settings dialog test connection behavior.
This replicates what happens when a user clicks "Test Connection" in the settings.
"""

from core.api_client import TF4MAPIClient

def test_settings_dialog_scenario():
    """
    Simulate what happens in the settings dialog:
    1. User has an existing client (possibly with old credentials)
    2. User enters new credentials (wrong ones)
    3. User clicks "Test Connection"
    """
    
    print("=" * 70)
    print("SIMULATING SETTINGS DIALOG TEST CONNECTION")
    print("=" * 70)
    print()
    
    # Scenario 1: Fresh client with wrong credentials
    print("Scenario 1: Fresh client, wrong credentials")
    print("-" * 70)
    
    client = TF4MAPIClient(
        base_url="https://toothfairy4m.ing.unimore.it",
        username="wrong_user",
        password="wrong_pass"
    )
    
    success, message = client.test_connection()
    print(f"Result: {'✅ PASS' if not success else '❌ FAIL'} - Should be FAILED")
    print(f"Message: {message}")
    print()
    
    # Scenario 2: Changing credentials to wrong ones
    print("Scenario 2: Existing client, change to wrong credentials")
    print("-" * 70)
    
    client2 = TF4MAPIClient(
        base_url="https://toothfairy4m.ing.unimore.it",
        username="any_user",  # Start with any credentials
        password="any_pass"
    )
    
    # Simulate what settings dialog does
    old_url = client2.base_url
    old_username = client2.username
    old_password = client2.password
    
    # Change to wrong credentials
    client2.set_base_url("https://toothfairy4m.ing.unimore.it")
    client2.set_credentials("wrong_user_2", "wrong_pass_2")
    
    success, message = client2.test_connection()
    print(f"Result: {'✅ PASS' if not success else '❌ FAIL'} - Should be FAILED")
    print(f"Message: {message}")
    print()
    
    # Restore
    client2.set_base_url(old_url)
    client2.set_credentials(old_username, old_password)
    
    # Scenario 3: Multiple attempts with wrong credentials
    print("Scenario 3: Multiple test attempts with same wrong credentials")
    print("-" * 70)
    
    client3 = TF4MAPIClient(
        base_url="https://toothfairy4m.ing.unimore.it",
        username="persistent_wrong_user",
        password="persistent_wrong_pass"
    )
    
    for i in range(3):
        success, message = client3.test_connection()
        result_str = '✅ PASS' if not success else '❌ FAIL'
        print(f"Attempt {i+1}: {result_str} - Message: {message}")
    
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("All scenarios should show FAILED for wrong credentials.")
    print("If any show SUCCESS, the bug is still present.")

if __name__ == "__main__":
    test_settings_dialog_scenario()
