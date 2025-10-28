"""
Test script to debug the login issue with wrong credentials.
"""

import requests
import sys

def test_wrong_login(base_url, wrong_username, wrong_password):
    """Test login with wrong credentials to see what happens."""
    
    session = requests.Session()
    print(f"Testing login to: {base_url}")
    print(f"Username: {wrong_username}")
    print(f"Password: {'*' * len(wrong_password)}\n")
    
    # Step 1: Get login page and CSRF token
    print("Step 1: Getting login page...")
    login_page = session.get(f"{base_url}/login/")
    print(f"  Status: {login_page.status_code}")
    print(f"  Cookies after GET: {dict(session.cookies)}")
    
    csrf_token = session.cookies.get('csrftoken')
    print(f"  CSRF Token: {csrf_token}\n")
    
    if not csrf_token:
        print("ERROR: No CSRF token received!")
        return
    
    # Step 2: Attempt login with WRONG credentials
    print("Step 2: Attempting login with WRONG credentials...")
    login_data = {
        'username': wrong_username,
        'password': wrong_password,
        'csrfmiddlewaretoken': csrf_token
    }
    
    headers = {
        'Referer': f"{base_url}/login/",
        'X-CSRFToken': csrf_token
    }
    
    login_response = session.post(
        f"{base_url}/login/", 
        data=login_data,
        headers=headers,
        allow_redirects=False
    )
    
    print(f"  Status: {login_response.status_code}")
    print(f"  Cookies after POST: {dict(session.cookies)}")
    print(f"  Has sessionid: {'sessionid' in session.cookies}")
    print(f"  Response URL: {login_response.url if hasattr(login_response, 'url') else 'N/A'}")
    
    # Check if there's a Location header (redirect)
    if 'Location' in login_response.headers:
        print(f"  Redirect Location: {login_response.headers['Location']}")
    
    # Check response content for error messages
    content_preview = login_response.text[:500]
    if 'error' in content_preview.lower() or 'invalid' in content_preview.lower():
        print(f"  Found error in response: {content_preview[:200]}...")
    
    print()
    
    # Step 3: Try to access protected API endpoint
    print("Step 3: Testing access to patients API...")
    test_response = session.get(f"{base_url}/api/maxillo/patients/")
    print(f"  Status: {test_response.status_code}")
    print(f"  Response length: {len(test_response.text)}")
    
    if test_response.status_code == 200:
        print(f"  WARNING: API returned 200! This is the bug!")
        print(f"  Response preview: {test_response.text[:300]}")
    elif test_response.status_code == 403:
        print(f"  Good: API returned 403 (forbidden)")
    elif test_response.status_code == 401:
        print(f"  Good: API returned 401 (unauthorized)")
    else:
        print(f"  Unexpected status: {test_response.status_code}")

if __name__ == "__main__":
    # Test with the TF4M server
    base_url = "https://toothfairy4m.ing.unimore.it"
    wrong_username = "wrong_user_test_12345"
    wrong_password = "wrong_password_test_12345"
    
    test_wrong_login(base_url, wrong_username, wrong_password)
