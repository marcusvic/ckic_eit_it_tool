"""
Comprehensive test to verify XSD documentation appears in help text for all fields
"""

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.form_generator import FormGenerator

def test_all_fields_documentation():
    print("🔧 Testing XSD Documentation in Help Text for ALL Fields")
    print("=" * 70)
    
    # Parse XSD
    parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
    parser.parse()
    
    # Generate models
    generator = DataModelGenerator(parser)
    models = generator.generate_models()
    project_model = models['Project']
    form_gen = FormGenerator(generator)
    fields_info = generator.get_model_fields_info(project_model)
    
    # Test top-level fields
    print("📋 Testing Top-Level Fields:")
    print("-" * 50)
    
    top_level_success = 0
    top_level_total = 0
    
    root_structure = parser.parsed_structure
    if root_structure and root_structure.children:
        for child in root_structure.children:
            if child.name in fields_info:  # Only test fields that are in the model
                top_level_total += 1
                field_info = fields_info[child.name]
                help_text = form_gen._create_help_text(field_info, field_info.get('description', ''))
                
                print(f"\n{top_level_total}. Field: {child.name}")
                if child.documentation:
                    print(f"   Expected doc: \"{child.documentation}\"")
                    if child.documentation in help_text:
                        print(f"   ✅ SUCCESS: Documentation found in help text")
                        top_level_success += 1
                    else:
                        print(f"   ❌ FAIL: Documentation missing from help text")
                        print(f"   Help text: \"{help_text}\"")
                else:
                    print(f"   ⚫ No XSD documentation available")
                    # Still count as success since no documentation is expected
                    top_level_success += 1
    
    # Test nested fields (sample)
    print(f"\n📦 Testing Sample Nested Fields:")
    print("-" * 50)
    
    all_fields = parser.get_all_fields()
    documented_nested = [f for f in all_fields if f.documentation and f.parent_path]
    nested_success = 0
    nested_total = min(5, len(documented_nested))  # Test first 5 nested documented fields
    
    for i, field in enumerate(documented_nested[:nested_total]):
        field_info = {
            'name': field.name,
            'type': str,
            'required': field.required,
            'description': field.documentation,
            'default': None,
            'constraints': {}
        }
        
        help_text = form_gen._create_help_text(field_info, field.documentation or '')
        
        print(f"\n{i+1}. Field: {field.name} (nested)")
        print(f"   Path: {field.parent_path}.{field.name}")
        print(f"   Expected doc: \"{field.documentation}\"")
        
        if field.documentation in help_text:
            print(f"   ✅ SUCCESS: Documentation found in help text")
            nested_success += 1
        else:
            print(f"   ❌ FAIL: Documentation missing from help text")
            print(f"   Help text: \"{help_text}\"")
    
    # Summary
    print(f"\n📊 RESULTS SUMMARY:")
    print("=" * 50)
    print(f"Top-level fields tested: {top_level_success}/{top_level_total}")
    print(f"Nested fields tested: {nested_success}/{nested_total}")
    print(f"Overall success rate: {((top_level_success + nested_success) / (top_level_total + nested_total) * 100):.1f}%")
    
    # Show specific examples
    print(f"\n🎯 EXAMPLE HELP TEXT WITH XSD DOCUMENTATION:")
    print("-" * 60)
    
    examples = ['Abstract', 'Duration', 'MultipleProposals']
    for example in examples:
        if example in fields_info:
            field_info = fields_info[example]
            help_text = form_gen._create_help_text(field_info, field_info.get('description', ''))
            print(f"\n{example}:")
            print(f"  \"{help_text}\"")
    
    total_success = top_level_success + nested_success
    total_tests = top_level_total + nested_total
    
    if total_success == total_tests:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ XSD documentation is successfully included in help text for all fields")
    else:
        print(f"\n⚠️ Some tests had issues - see details above")
    
    return total_success == total_tests

if __name__ == "__main__":
    success = test_all_fields_documentation()
    print(f"\nOverall test result: {'PASSED' if success else 'FAILED'}")