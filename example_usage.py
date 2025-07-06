"""
Example usage of the EIT Tool core functionality.
This script demonstrates how to use the tool programmatically.
"""

import os
from datetime import date
from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.xml_engine import XMLEngine


def main():
    """Main example function"""
    print("🚀 EIT Tool - Example Usage")
    print("=" * 50)
    
    # Check if XSD file exists
    xsd_path = "EIT IT Tool - Extended_projects_v1.16.xsd"
    if not os.path.exists(xsd_path):
        print(f"❌ XSD file not found: {xsd_path}")
        print("Please ensure the XSD file is in the current directory.")
        return
    
    try:
        # Step 1: Parse XSD Schema
        print("\n📋 Step 1: Parsing XSD Schema...")
        xsd_parser = XSDParser(xsd_path)
        parsed_data = xsd_parser.parse()
        
        print(f"✅ Schema parsed successfully!")
        print(f"   Root element: {parsed_data['root_element']}")
        print(f"   Namespace: {parsed_data.get('namespace', 'None')}")
        
        # Step 2: Generate Data Models
        print("\n🏗️  Step 2: Generating Data Models...")
        data_model_generator = DataModelGenerator(xsd_parser)
        models = data_model_generator.generate_models()
        
        print(f"✅ {len(models)} model(s) generated successfully!")
        
        # Step 3: Create Sample Data
        print("\n📝 Step 3: Creating Sample Data...")
        root_model = models[parsed_data['root_element']]
        
        # Create sample project data
        sample_data = {
            "Abstract": "This is a sample project for demonstration purposes.",
            "Acronym": "SAMPLE",
            "ActionType": "HORIZON-EIT-KIC",
            "CallId": "SAMPLE-CALL-2024",
            "Duration": 24,
            "EndDate": date(2026, 12, 31),
            "NbParticipants": 5,
            "ProjectTitle": "Sample EIT Project",
            "SignatureDate": date(2024, 1, 1),
            "StartDate": date(2024, 1, 1),
            "Status": "Active"
        }
        
        # Create model instance
        try:
            model_instance = root_model(**sample_data)
            print("✅ Sample model instance created successfully!")
        except Exception as e:
            print(f"⚠️  Some fields might be missing or invalid: {e}")
            # Create a minimal valid instance
            minimal_data = {
                "Abstract": "Sample project",
                "Acronym": "SAMPLE",
                "ActionType": "HORIZON-EIT-KIC",
                "CallId": "SAMPLE-CALL",
                "Duration": 12,
                "EndDate": date(2025, 12, 31),
                "NbParticipants": 1,
                "ProjectTitle": "Sample Project",
                "SignatureDate": date(2024, 1, 1),
                "StartDate": date(2024, 1, 1),
                "Status": "Active"
            }
            model_instance = root_model(**minimal_data)
            print("✅ Minimal model instance created successfully!")
        
        # Step 4: Generate XML
        print("\n🔧 Step 4: Generating XML...")
        xml_engine = XMLEngine(xsd_parser)
        
        xml_content, is_valid, validation_errors = xml_engine.generate_and_validate(
            model_instance, pretty_print=True
        )
        
        print(f"✅ XML generated successfully!")
        print(f"   Valid: {is_valid}")
        
        if validation_errors:
            print("   Validation errors:")
            for error in validation_errors:
                print(f"     - {error}")
        
        # Step 5: Display XML Preview
        print("\n📄 Step 5: XML Preview (first 500 characters):")
        print("-" * 50)
        print(xml_content[:500])
        if len(xml_content) > 500:
            print("...")
        print("-" * 50)
        
        # Step 6: Save XML to file
        print("\n💾 Step 6: Saving XML to file...")
        output_filename = "sample_project_output.xml"
        xml_engine.save_xml_to_file(xml_content, output_filename)
        print(f"✅ XML saved to: {output_filename}")
        
        print("\n🎉 Example completed successfully!")
        print("\nNext steps:")
        print("- Run 'streamlit run app.py' to use the web interface")
        print("- Run 'python api/api_interface.py' to start the API server")
        print("- Modify the sample data above to test different scenarios")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        print("Please check the XSD file and try again.")


if __name__ == "__main__":
    main()