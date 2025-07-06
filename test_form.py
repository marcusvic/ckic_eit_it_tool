"""
Test script to verify form generation works correctly
"""

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.form_generator import FormGenerator

def test_form_generation():
    print("🧪 Testing Form Generation")
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
    
    # Test specific fields
    test_fields = ['ActionType', 'PartnershipName', 'Abstract', 'Duration']
    
    for field_name in test_fields:
        field_info = fields_info.get(field_name)
        if field_info:
            field_type = field_info['type']
            help_text = form_gen._create_help_text(field_info, field_info.get('description', ''))
            
            print(f"\n📝 Field: {field_name}")
            print(f"   Type: {field_type}")
            print(f"   Required: {field_info['required']}")
            print(f"   Help: {help_text}")
            
            # Check if it's an enumeration
            if hasattr(field_type, '__origin__'):
                from typing import Literal
                if field_type.__origin__ is Literal:
                    print(f"   🎯 ENUMERATION: {list(field_type.__args__)}")
    
    print("\n🎉 Form generation test completed successfully!")

if __name__ == "__main__":
    test_form_generation()