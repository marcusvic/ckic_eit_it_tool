"""
Test script to verify that the app now only uses hierarchical form
"""

import re

def test_hierarchical_only():
    print("🔧 Verifying Hierarchical Form Only Implementation")
    print("=" * 60)
    
    # Read the main app file
    with open('app.py', 'r') as f:
        app_content = f.read()
    
    # Check that form style selection is removed
    checks = [
        {
            'name': 'Form style radio button removed',
            'pattern': r'st\.radio.*form.*style',
            'should_exist': False
        },
        {
            'name': 'Simple form conditional removed',
            'pattern': r'if.*form_type.*==.*Simple Form',
            'should_exist': False
        },
        {
            'name': 'Hierarchical form conditional removed',
            'pattern': r'if.*form_type.*==.*Hierarchical Form',
            'should_exist': False
        },
        {
            'name': 'Always uses complex form generator',
            'pattern': r'complex_form_generator\.create_complex_form_sections',
            'should_exist': True
        },
        {
            'name': 'No simple form generator usage in main flow',
            'pattern': r'form_generator\.create_form_sections',
            'should_exist': False
        }
    ]
    
    results = []
    
    for check in checks:
        pattern_found = bool(re.search(check['pattern'], app_content, re.IGNORECASE))
        
        if check['should_exist']:
            success = pattern_found
            status = "✅ PASS" if success else "❌ FAIL"
            message = f"Found: {check['pattern']}" if success else f"Missing: {check['pattern']}"
        else:
            success = not pattern_found
            status = "✅ PASS" if success else "❌ FAIL"
            message = f"Correctly removed: {check['pattern']}" if success else f"Still exists: {check['pattern']}"
        
        results.append(success)
        print(f"{status} {check['name']}")
        print(f"      {message}")
    
    # Check the new streamlined tab content
    print(f"\n📝 Checking Updated Tab Content:")
    
    if 'st.subheader("📝 Data Entry Form")' in app_content:
        print("✅ PASS Updated tab header")
    else:
        print("❌ FAIL Tab header not updated")
        results.append(False)
    
    if 'Always use hierarchical form' in app_content:
        print("✅ PASS Comment indicates hierarchical-only approach")
        results.append(True)
    else:
        print("⚠️  INFO No comment found (but that's okay)")
        results.append(True)
    
    # Summary
    success_count = sum(results)
    total_checks = len(results)
    
    print(f"\n📊 Results Summary:")
    print(f"   Tests passed: {success_count}/{total_checks}")
    print(f"   Success rate: {(success_count/total_checks)*100:.1f}%")
    
    if success_count == total_checks:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Form style selection logic successfully removed")
        print(f"✅ App now always uses hierarchical form")
        print(f"✅ User interface simplified")
    else:
        print(f"\n⚠️ Some checks failed - see details above")
    
    return success_count == total_checks

if __name__ == "__main__":
    success = test_hierarchical_only()
    print(f"\nVerification {'PASSED' if success else 'FAILED'}")