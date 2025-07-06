"""
Simple Streamlit app to test that XSD documentation appears in help text
"""

import streamlit as st
from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.complex_form_generator import ComplexFormGenerator

def main():
    st.title("🧪 XSD Documentation in Help Text Test")
    
    # Parse XSD
    parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
    parser.parse()
    
    # Get documented fields
    documented_fields = [f for f in parser.get_all_fields() if f.documentation]
    
    st.subheader("📚 Documented Fields Found")
    st.write(f"Found {len(documented_fields)} fields with documentation:")
    
    for i, field in enumerate(documented_fields[:5]):
        st.write(f"{i+1}. **{field.name}**: {field.documentation}")
    
    if len(documented_fields) > 5:
        st.write(f"... and {len(documented_fields) - 5} more")
    
    st.subheader("🎯 Help Text Demonstration")
    
    # Create form generator
    generator = DataModelGenerator(parser)
    complex_form_gen = ComplexFormGenerator(parser, generator)
    
    # Test with first documented field
    if documented_fields:
        test_field = documented_fields[0]
        
        st.write(f"**Testing with field: {test_field.name}**")
        st.write(f"Expected documentation: *{test_field.documentation}*")
        
        # Create field info
        field_info = {
            'name': test_field.name,
            'type': str,
            'required': test_field.required,
            'description': test_field.documentation,
            'default': None,
            'constraints': {}
        }
        
        # Generate help text
        help_text = complex_form_gen.base_form_generator._create_help_text(field_info, test_field.documentation or '')
        
        st.write(f"**Generated help text:**")
        st.info(help_text)
        
        if test_field.documentation in help_text:
            st.success("✅ XSD Documentation successfully included in help text!")
        else:
            st.error("❌ XSD Documentation missing from help text")
        
        # Create actual widget to show help text
        st.subheader("📝 Sample Widget with Help Text")
        st.text_input(
            label=f"{test_field.name}",
            help=help_text,
            key="demo_widget"
        )
        
        st.markdown("*Hover over the ⓘ icon next to the field above to see the help text with XSD documentation*")
    
    else:
        st.warning("No documented fields found in the XSD")

if __name__ == "__main__":
    main()