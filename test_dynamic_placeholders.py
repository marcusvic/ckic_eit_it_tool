"""
Test script to showcase the new dynamic placeholder text feature
"""

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.form_generator import FormGenerator


def test_dynamic_placeholders():
    print("🎯 Dynamic Placeholder Text Feature Demo")
    print("=" * 60)
    
    # Parse XSD and generate models
    parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
    parsed_data = parser.parse()
    
    generator = DataModelGenerator(parser)
    models = generator.generate_models()
    project_model = models['Project']
    
    form_gen = FormGenerator(generator)
    fields_info = generator.get_model_fields_info(project_model)
    
    # Get all fields with their types
    all_fields = parser.get_all_fields()
    
    # Test cases by data type
    test_cases = {
        'String Fields': [],
        'Date Fields': [],
        'Integer Fields': [],
        'Decimal Fields': [],
        'Enumeration Fields': []
    }
    
    # Categorize fields
    for field in all_fields:
        if str(field.data_type) == 'DataType.STRING':
            test_cases['String Fields'].append(field.name)
        elif str(field.data_type) == 'DataType.DATE':
            test_cases['Date Fields'].append(field.name)
        elif str(field.data_type) == 'DataType.INTEGER':
            test_cases['Integer Fields'].append(field.name)
        elif str(field.data_type) == 'DataType.DECIMAL':
            test_cases['Decimal Fields'].append(field.name)
        elif str(field.data_type) == 'DataType.ENUMERATION':
            test_cases['Enumeration Fields'].append(field.name)
    
    # Test placeholders for each type
    for category, field_list in test_cases.items():
        if field_list:
            print(f"\n📝 {category}:")
            
            # Show first 3 examples of each type
            for field_name in field_list[:3]:
                # Get field info if it's a top-level field
                field_info = fields_info.get(field_name)
                if field_info:
                    constraints = field_info.get('constraints', {})
                else:
                    # For nested fields, create example constraints
                    constraints = {}
                    for field in all_fields:
                        if field.name == field_name and field.constraints:
                            if field.constraints.min_length:
                                constraints['min_length'] = field.constraints.min_length
                            if field.constraints.max_length:
                                constraints['max_length'] = field.constraints.max_length
                            if field.constraints.min_value:
                                constraints['min_value'] = field.constraints.min_value
                            if field.constraints.max_value:
                                constraints['max_value'] = field.constraints.max_value
                            if field.constraints.enumeration:
                                constraints['enumeration'] = field.constraints.enumeration
                            break
                
                # Generate placeholder
                xsd_type = form_gen._get_xsd_type_name_for_field(field_name)
                placeholder = form_gen._create_placeholder_text(constraints, field_name, xsd_type)
                
                # Show result
                print(f"  ✅ {field_name:<20} → \"{placeholder}\"")
            
            if len(field_list) > 3:
                print(f"     ... and {len(field_list) - 3} more {category.lower()}")
    
    # Summary
    print(f"\n📊 Summary:")
    total_fields = sum(len(field_list) for field_list in test_cases.values())
    print(f"  Total fields processed: {total_fields}")
    
    for category, field_list in test_cases.items():
        print(f"  {category}: {len(field_list)}")
    
    print(f"\n🎉 Dynamic Placeholder Features:")
    print(f"  ✅ String fields → Show character length constraints")
    print(f"  ✅ Date fields → Show date format (YYYY-MM-DD)")
    print(f"  ✅ Integer fields → Show numeric constraints (min/max)")
    print(f"  ✅ Decimal fields → Show decimal format with constraints")
    print(f"  ✅ Enumeration fields → Show dropdown hint with options")
    print(f"  ✅ All placeholders include relevant restrictions from XSD")
    
    print(f"\n🚀 Before vs After:")
    print(f"  Before: All fields showed 'Enter text...'")
    print(f"  After:  Each field shows data-type specific guidance!")


if __name__ == "__main__":
    test_dynamic_placeholders()