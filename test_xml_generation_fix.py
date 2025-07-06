#!/usr/bin/env python3
"""
Test script to debug XML generation issues with list fields
"""

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.xml_engine import XMLEngine
from typing import get_type_hints

def test_model_conversion():
    """Test the model conversion process"""
    print("🔍 Testing XML Generation Fix...")
    
    # Initialize components
    xsd_parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
    parsed_data = xsd_parser.parse()
    
    data_model_generator = DataModelGenerator(xsd_parser)
    models = data_model_generator.generate_models()
    
    root_model = models[parsed_data['root_element']]
    xml_engine = XMLEngine(xsd_parser)
    
    # Sample form data with repeatable elements
    test_form_data = {
        'Abstract': 'Test Abstract',
        'Acronym': 'TEST123',
        'ActionType': 'Art 185',
        'CallId': 'TEST-CALL',
        'Duration': '24',
        'EndDate': '2024-12-31',
        'NbParticipants': '1',
        'ProjectTitle': 'Test Project',
        'Outputs': [
            {
                'Deliverable': 'Yes',
                'OutputDeliverableDescription': 'Test output 1',
                'OutputDeliverableName': 'Output 1'
            },
            {
                'Deliverable': 'No', 
                'OutputDeliverableDescription': 'Test output 2',
                'OutputDeliverableName': 'Output 2'
            }
        ]
    }
    
    print("\n📊 Form Data Structure:")
    print(f"Outputs type: {type(test_form_data['Outputs'])}")
    print(f"Outputs[0] type: {type(test_form_data['Outputs'][0])}")
    print(f"Outputs content: {test_form_data['Outputs']}")
    
    # Test model conversion
    print("\n🔄 Converting form data to model instance...")
    try:
        model_instance = xml_engine.create_model_instance_from_form_data(test_form_data, root_model)
        print("✅ Model instance created successfully")
        
        # Check the type of the Outputs field
        model_dict = model_instance.dict()
        if 'Outputs' in model_dict:
            outputs = model_dict['Outputs']
            print(f"\n📋 Model Outputs type: {type(outputs)}")
            if outputs:
                print(f"First output type: {type(outputs[0])}")
                print(f"Is first output BaseModel? {hasattr(outputs[0], '__dict__')}")
                print(f"First output content: {outputs[0]}")
        
        # Generate XML
        print("\n🔄 Generating XML...")
        xml_output = xml_engine.generate_xml(model_instance)
        
        # Check for dictionary patterns in XML
        if '[{' in xml_output:
            print("❌ Found dictionary patterns in XML output!")
            start_idx = xml_output.find('[{')
            end_idx = xml_output.find('}]', start_idx) + 2
            problematic_section = xml_output[max(0, start_idx-50):end_idx+50]
            print(f"Problematic section: {problematic_section}")
        else:
            print("✅ No dictionary patterns found in XML")
        
        # Show a snippet of the XML
        print(f"\n📄 XML Output snippet (first 500 chars):")
        print(xml_output[:500])
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Test completed")

if __name__ == "__main__":
    test_model_conversion()