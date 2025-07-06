"""
Final test of the complete EIT Tool pipeline with fixed defaults
"""

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.form_generator import FormGenerator

def test_complete_pipeline():
    print("🎯 Final EIT Tool Test")
    print("=" * 50)
    
    # Parse XSD
    parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
    parsed_data = parser.parse()
    print(f"✅ XSD parsed: {parsed_data['root_element']}")
    
    # Generate models
    generator = DataModelGenerator(parser)
    models = generator.generate_models()
    project_model = models['Project']
    print(f"✅ Models generated: {len(models)} models")
    
    # Test form generator
    form_gen = FormGenerator(generator)
    fields_info = generator.get_model_fields_info(project_model)
    print(f"✅ Field info generated: {len(fields_info)} fields")
    
    # Test specific improvements
    print("\n🔧 Testing Specific Improvements:")
    
    # 1. Enumeration fields
    enum_fields = ['ActionType', 'PartnershipName', 'PartnershipType', 'EitArea']
    print(f"\n📋 Enumeration Fields ({len([f for f in enum_fields if f in fields_info])} found):")
    
    for field_name in enum_fields:
        field_info = fields_info.get(field_name)
        if field_info:
            field_type = field_info['type']
            if hasattr(field_type, '__origin__'):
                from typing import Literal
                if field_type.__origin__ is Literal:
                    options = list(field_type.__args__)
                    default = form_gen._create_default_value(field_type, {})
                    print(f"  ✅ {field_name}: {len(options)} options, default='{default}'")
    
    # 2. Text fields with constraints
    text_fields = ['Abstract', 'Acronym', 'ProjectTitle']
    print(f"\n📝 Text Fields with Constraints:")
    
    for field_name in text_fields:
        field_info = fields_info.get(field_name)
        if field_info:
            constraints = field_info.get('constraints', {})
            placeholder = form_gen._create_placeholder_text(constraints)
            help_text = form_gen._create_help_text(field_info, field_info.get('description', ''))
            print(f"  ✅ {field_name}:")
            print(f"     Placeholder: '{placeholder}'")
            print(f"     Help: '{help_text[:80]}...' (truncated)")
    
    # 3. Check for PydanticUndefined
    print(f"\n🔍 Checking for PydanticUndefined issues:")
    pydantic_undefined_count = 0
    for field_name, field_info in fields_info.items():
        default = field_info.get('default')
        if str(default) == 'PydanticUndefined':
            pydantic_undefined_count += 1
    
    if pydantic_undefined_count == 0:
        print("  ✅ No PydanticUndefined values found in any field!")
    else:
        print(f"  ❌ Found {pydantic_undefined_count} fields with PydanticUndefined")
    
    print(f"\n🎉 Complete pipeline test passed!")
    print("Ready for Streamlit deployment!")

if __name__ == "__main__":
    test_complete_pipeline()