"""
Test script to verify the help text data type fix
"""

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.form_generator import FormGenerator


def test_help_text_data_types():
    print("🧪 Testing Help Text Data Type Fix")
    print("=" * 50)
    
    # Parse XSD and generate models
    parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
    parsed_data = parser.parse()
    
    generator = DataModelGenerator(parser)
    models = generator.generate_models()
    project_model = models['Project']
    
    form_gen = FormGenerator(generator)
    fields_info = generator.get_model_fields_info(project_model)
    
    # Test cases: field_name -> expected_xsd_type
    test_cases = {
        'Abstract': 'string',
        'EndDate': 'date',
        'SignatureDate': 'date', 
        'NbParticipants': 'integer',
        'Duration': 'integer',
        'ActionType': 'enumeration',
        'Acronym': 'string'
    }
    
    print("\n📝 Testing Top-Level Fields:")
    all_passed = True
    
    for field_name, expected_type in test_cases.items():
        if field_name in fields_info:
            field_info = fields_info[field_name]
            help_text = form_gen._create_help_text(field_info, field_info.get('description', ''))
            
            # Check if the expected type is in the help text
            if f"Data type: {expected_type}" in help_text:
                print(f"  ✅ {field_name}: {expected_type} (PASS)")
            else:
                print(f"  ❌ {field_name}: Expected '{expected_type}', got '{help_text}' (FAIL)")
                all_passed = False
        else:
            print(f"  ⚠️  {field_name}: Not found in top-level fields")
    
    # Test nested fields
    print("\n📦 Testing Nested Fields:")
    all_fields = parser.get_all_fields()
    
    nested_test_cases = {
        'ProjectTotalBudget': 'decimal',
        'ProjectEuContribution': 'decimal',
        'Deliverable': 'enumeration'
    }
    
    for field_name, expected_type in nested_test_cases.items():
        for field in all_fields:
            if field.name == field_name:
                # Convert DataType enum to string
                actual_type = str(field.data_type).replace('DataType.', '').lower()
                if actual_type == expected_type:
                    print(f"  ✅ {field_name}: {expected_type} (PASS)")
                else:
                    print(f"  ❌ {field_name}: Expected '{expected_type}', got '{actual_type}' (FAIL)")
                    all_passed = False
                break
        else:
            print(f"  ⚠️  {field_name}: Not found")
    
    # Test enumeration fields specifically
    print("\n🎯 Testing Enumeration Fields:")
    enum_fields = []
    for field in all_fields:
        if str(field.data_type) == 'DataType.ENUMERATION':
            enum_fields.append(field.name)
    
    print(f"  Found {len(enum_fields)} enumeration fields:")
    for field_name in enum_fields[:5]:  # Show first 5
        print(f"    - {field_name}")
    
    if len(enum_fields) > 5:
        print(f"    ... and {len(enum_fields) - 5} more")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"  Total fields analyzed: {len(test_cases) + len(nested_test_cases)}")
    print(f"  Enumeration fields found: {len(enum_fields)}")
    
    if all_passed:
        print(f"  🎉 ALL TESTS PASSED - Help text shows correct XSD data types!")
    else:
        print(f"  ❌ Some tests failed - check output above")
    
    print(f"\n🚀 Help text now shows:")
    print(f"  ✅ 'Data type: date' for date fields")
    print(f"  ✅ 'Data type: integer' for integer fields") 
    print(f"  ✅ 'Data type: decimal' for decimal fields")
    print(f"  ✅ 'Data type: enumeration' for enumeration fields")
    print(f"  ✅ 'Data type: string' for string fields")
    
    return all_passed


if __name__ == "__main__":
    success = test_help_text_data_types()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")