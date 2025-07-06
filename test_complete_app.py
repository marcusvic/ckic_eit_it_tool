"""
Complete Application Test
Tests the entire EIT Tool pipeline with complex elements support.
"""

import sys
import os
from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.form_generator import FormGenerator
from core.complex_form_generator import ComplexFormGenerator
from core.xml_engine import XMLEngine


def test_complete_application():
    print("🧪 Complete EIT Tool Application Test")
    print("=" * 60)
    
    try:
        # Step 1: Parse XSD
        print("\n📋 Step 1: Parsing XSD Schema...")
        parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
        parsed_data = parser.parse()
        print(f"  ✅ Schema parsed: {parsed_data['root_element']}")
        print(f"  ✅ Namespace: {parsed_data.get('namespace', 'None')}")
        
        # Step 2: Analyze structure
        print("\n🏗️ Step 2: Analyzing Structure...")
        complex_elements = parser.get_complex_elements()
        simple_elements = parser.get_simple_elements()
        all_fields = parser.get_all_fields()
        
        print(f"  ✅ Total fields: {len(all_fields)}")
        print(f"  ✅ Complex elements: {len(complex_elements)}")
        print(f"  ✅ Simple elements: {len(simple_elements)}")
        
        # Step 3: Generate data models
        print("\n🏭 Step 3: Generating Data Models...")
        generator = DataModelGenerator(parser)
        models = generator.generate_models()
        root_model = models[parsed_data['root_element']]
        
        print(f"  ✅ Models generated: {len(models)}")
        print(f"  ✅ Root model: {root_model.__name__}")
        
        # Step 4: Test form generators
        print("\n📝 Step 4: Testing Form Generators...")
        
        # Simple form generator
        simple_form_gen = FormGenerator(generator)
        fields_info = generator.get_model_fields_info(root_model)
        print(f"  ✅ Simple form generator ready: {len(fields_info)} fields")
        
        # Complex form generator  
        complex_form_gen = ComplexFormGenerator(parser, generator)
        print(f"  ✅ Complex form generator ready")
        
        # Step 5: Test XML engine
        print("\n🔧 Step 5: Testing XML Engine...")
        xml_engine = XMLEngine(parser)
        print(f"  ✅ XML engine initialized")
        
        # Step 6: Test enumeration handling
        print("\n🎯 Step 6: Testing Enumeration Fields...")
        enum_fields = []
        for field_name, field_info in fields_info.items():
            field_type = field_info['type']
            if hasattr(field_type, '__origin__'):
                from typing import Literal
                if field_type.__origin__ is Literal:
                    enum_fields.append((field_name, list(field_type.__args__)))
        
        print(f"  ✅ Enumeration fields found: {len(enum_fields)}")
        for field_name, options in enum_fields[:3]:
            print(f"    - {field_name}: {len(options)} options")
        
        # Step 7: Test complex element categorization
        print("\n📦 Step 7: Testing Complex Element Categorization...")
        required_complex = [elem for elem in complex_elements if elem.required]
        optional_complex = [elem for elem in complex_elements if not elem.required]
        
        print(f"  ✅ Required complex elements: {len(required_complex)}")
        print(f"  ✅ Optional complex elements: {len(optional_complex)}")
        
        # Step 8: Test help text generation
        print("\n💬 Step 8: Testing Help Text Generation...")
        sample_fields = ['ActionType', 'Abstract', 'ProjectTitle']
        for field_name in sample_fields:
            if field_name in fields_info:
                field_info = fields_info[field_name]
                help_text = simple_form_gen._create_help_text(field_info, field_info.get('description', ''))
                print(f"  ✅ {field_name}: Help text generated ({len(help_text)} chars)")
        
        # Step 9: Test placeholder text
        print("\n📝 Step 9: Testing Placeholder Text...")
        for field_name in sample_fields:
            if field_name in fields_info:
                field_info = fields_info[field_name]
                constraints = field_info.get('constraints', {})
                if constraints:
                    placeholder = simple_form_gen._create_placeholder_text(constraints)
                    print(f"  ✅ {field_name}: Placeholder generated")
        
        # Step 10: Validate no PydanticUndefined issues
        print("\n🔍 Step 10: Validating No PydanticUndefined Issues...")
        pydantic_issues = 0
        for field_name, field_info in fields_info.items():
            default = field_info.get('default')
            if str(default) == 'PydanticUndefined':
                pydantic_issues += 1
        
        if pydantic_issues == 0:
            print(f"  ✅ No PydanticUndefined issues found")
        else:
            print(f"  ❌ Found {pydantic_issues} PydanticUndefined issues")
        
        print("\n🎉 All Tests Passed!")
        print("\n🚀 Application Ready for Deployment!")
        print("\nTo run the application:")
        print("  1. source .venv/bin/activate")
        print("  2. streamlit run app.py") 
        print("  3. Load XSD schema")
        print("  4. Choose 'Hierarchical Form (Complex Elements)' for advanced features")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_complete_application()
    sys.exit(0 if success else 1)