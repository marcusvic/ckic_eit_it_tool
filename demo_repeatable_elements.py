"""
Demo script to showcase the new repeatable elements functionality
Run with: streamlit run demo_repeatable_elements.py
"""

import streamlit as st
from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.complex_form_generator import ComplexFormGenerator

def main():
    st.title("🔄 Repeatable Elements Demo")
    st.markdown("Demonstration of new functionality for handling elements with maxOccurs > 1")
    
    # Parse XSD
    if 'demo_parser' not in st.session_state:
        st.session_state.demo_parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
        st.session_state.demo_parser.parse()
        
        st.session_state.demo_generator = DataModelGenerator(st.session_state.demo_parser)
        st.session_state.demo_complex_form = ComplexFormGenerator(
            st.session_state.demo_parser, 
            st.session_state.demo_generator
        )
    
    # Show repeatable elements summary
    st.subheader("📊 Repeatable Elements Found")
    
    all_fields = st.session_state.demo_parser.get_all_fields()
    repeatable_fields = [f for f in all_fields if st.session_state.demo_complex_form._is_repeatable_element(f)]
    
    st.write(f"Found **{len(repeatable_fields)}** repeatable elements:")
    
    for field in repeatable_fields[:8]:  # Show first 8
        max_text = "unlimited" if field.max_occurs is None else str(field.max_occurs)
        st.write(f"• **{field.name}**: {field.min_occurs} to {max_text} instances")
    
    if len(repeatable_fields) > 8:
        st.write(f"... and {len(repeatable_fields) - 8} more")
    
    # Demo section selection
    st.subheader("🎯 Demo Section")
    
    demo_sections = {
        "Outputs (Output elements)": "Output",
        "EIT KPIs (KPI elements)": "KPI", 
        "Project Actual Costs (YearData elements)": "YearData"
    }
    
    selected_demo = st.selectbox("Choose a section to demo:", list(demo_sections.keys()))
    target_element = demo_sections[selected_demo]
    
    st.markdown("---")
    
    # Find and demo the selected element
    for field in repeatable_fields:
        if field.name == target_element:
            st.subheader(f"📋 Demo: {field.name} (Repeatable Element)")
            
            st.info(f"""
            **Element Info:**
            - **Name**: {field.name}
            - **Min instances**: {field.min_occurs}
            - **Max instances**: {"unlimited" if field.max_occurs is None else field.max_occurs}
            - **Required**: {field.required}
            - **Documentation**: {field.documentation or "None"}
            """)
            
            st.markdown("**Key Features:**")
            st.markdown("• ➕ **Add button** to create new instances")
            st.markdown("• ➖ **Remove button** to delete instances (respects minimum)")
            st.markdown("• 📄 **Numbered instances** for clarity")
            st.markdown("• ⚠️ **Validation** for min/max constraints")
            st.markdown("• 🔑 **Unique keys** for each instance to prevent conflicts")
            
            if field.children:
                st.markdown(f"**Child elements** ({len(field.children)}):")
                for child in field.children[:5]:
                    st.markdown(f"  • {child.name} ({child.data_type.value})")
                if len(field.children) > 5:
                    st.markdown(f"  • ... and {len(field.children) - 5} more")
            
            # Note about full implementation
            st.warning("""
            **Note**: This is a demo showing the technical implementation. 
            The full interactive form with add/remove buttons is available in the main application.
            Run the main app.py to see the complete functionality in action!
            """)
            
            break
    
    # Implementation summary
    st.subheader("🛠️ Implementation Summary")
    st.markdown("""
    **What was implemented:**
    
    1. **Enhanced XSD Parser** to capture minOccurs/maxOccurs from sequence elements
    2. **Updated SchemaField** to store occurrence information  
    3. **New ComplexFormGenerator methods** for repeatable element handling:
       - `_is_repeatable_element()` - detects elements with maxOccurs > 1
       - `_process_repeatable_field()` - renders add/remove UI and multiple instances
       - Session state management for instance counts
    4. **Dynamic UI** with add/remove buttons and instance numbering
    5. **Validation** for minimum/maximum instance constraints
    
    **Key Benefits:**
    - Users can now add multiple Outputs, KPIs, YearData entries, etc.
    - Proper validation ensures schema compliance
    - Intuitive UI with clear instance management
    - Maintains existing functionality for non-repeatable elements
    """)

if __name__ == "__main__":
    main()