"""
EIT Tool - Main Streamlit Application
Dynamic XML generation tool based on XSD schemas.
"""

import streamlit as st
import os
from typing import Dict, Any, Optional
from datetime import datetime
import tempfile

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.form_generator import FormGenerator
from core.complex_form_generator import ComplexFormGenerator
from core.xml_engine import XMLEngine


def initialize_session_state():
    """Initialize session state variables"""
    if 'xsd_parser' not in st.session_state:
        st.session_state.xsd_parser = None
    if 'data_model_generator' not in st.session_state:
        st.session_state.data_model_generator = None
    if 'form_generator' not in st.session_state:
        st.session_state.form_generator = None
    if 'complex_form_generator' not in st.session_state:
        st.session_state.complex_form_generator = None
    if 'xml_engine' not in st.session_state:
        st.session_state.xml_engine = None
    if 'root_model' not in st.session_state:
        st.session_state.root_model = None
    if 'current_xsd_path' not in st.session_state:
        st.session_state.current_xsd_path = None


def load_xsd_schema(xsd_path: str) -> bool:
    """Load and parse XSD schema"""
    try:
        # Initialize parser
        xsd_parser = XSDParser(xsd_path)
        parsed_data = xsd_parser.parse()
        
        # Initialize data model generator
        data_model_generator = DataModelGenerator(xsd_parser)
        models = data_model_generator.generate_models()
        
        # Get root model
        root_model = models[parsed_data['root_element']]
        
        # Initialize form generator
        form_generator = FormGenerator(data_model_generator)
        
        # Initialize complex form generator
        complex_form_generator = ComplexFormGenerator(xsd_parser, data_model_generator)
        
        # Initialize XML engine
        xml_engine = XMLEngine(xsd_parser)
        
        # Store in session state
        st.session_state.xsd_parser = xsd_parser
        st.session_state.data_model_generator = data_model_generator
        st.session_state.form_generator = form_generator
        st.session_state.complex_form_generator = complex_form_generator
        st.session_state.xml_engine = xml_engine
        st.session_state.root_model = root_model
        st.session_state.current_xsd_path = xsd_path
        
        return True
        
    except Exception as e:
        st.error(f"Failed to load XSD schema: {str(e)}")
        return False


def main():
    """Main application function"""
    st.set_page_config(
        page_title="EIT Tool - Dynamic XML Generator",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()
    
    # Header
    st.title("🏭 EIT Tool - Dynamic XML Generator")
    st.markdown("Generate XML files from XSD schemas with a user-friendly interface")
    
    # Sidebar for XSD loading
    with st.sidebar:
        st.header("📋 Schema Configuration")
        
        # XSD file selection
        xsd_option = st.radio(
            "Select XSD Source:",
            ["Use existing XSD file", "Upload new XSD file"]
        )
        
        if xsd_option == "Use existing XSD file":
            # Look for XSD files in current directory
            xsd_files = [f for f in os.listdir('.') if f.endswith('.xsd')]
            if xsd_files:
                selected_xsd = st.selectbox("Select XSD file:", xsd_files)
                if st.button("Load Schema"):
                    if load_xsd_schema(selected_xsd):
                        st.success("Schema loaded successfully!")
                        st.rerun()
            else:
                st.warning("No XSD files found in current directory")
        
        else:
            # Upload XSD file
            uploaded_xsd = st.file_uploader("Upload XSD file", type=['xsd'])
            if uploaded_xsd is not None:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xsd') as tmp_file:
                    tmp_file.write(uploaded_xsd.getvalue())
                    tmp_path = tmp_file.name
                
                if st.button("Load Uploaded Schema"):
                    if load_xsd_schema(tmp_path):
                        st.success("Schema loaded successfully!")
                        st.rerun()
        
        # Show current schema info
        if st.session_state.xsd_parser:
            st.subheader("📊 Current Schema")
            st.info(f"Root Element: {st.session_state.xsd_parser.root_element.name}")
            st.info(f"File: {os.path.basename(st.session_state.current_xsd_path)}")
    
    # Main content area
    if st.session_state.root_model is None:
        st.info("👆 Please load an XSD schema to begin")
        
        # Show sample or documentation
        st.subheader("📖 About EIT Tool")
        st.markdown("""
        This tool allows you to:
        - **Load XSD schemas** dynamically
        - **Generate forms** automatically based on schema structure
        - **Validate data** in real-time
        - **Generate XML** files that conform to your schema
        - **Export** XML files for use in other systems
        """)
        
        return
    
    # Tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Data Entry", "🔍 Preview", "✅ Validate", "📁 Export"])
    
    with tab1:
        st.subheader("📝 Data Entry Form")
        
        # Always use hierarchical form
        form_data = st.session_state.complex_form_generator.create_complex_form_sections()
        
        # Show form completion status
        if form_data:
            stats = st.session_state.complex_form_generator.get_form_completion_stats(form_data)
            
            st.progress(stats['completion_percentage'] / 100)
            st.caption(
                f"Form completion: {stats['filled_fields']}/{stats['total_fields']} fields "
                f"({stats['completion_percentage']:.1f}%) - {stats['remaining_fields']} remaining"
            )
            
            # Validation
            is_valid, errors = st.session_state.complex_form_generator.validate_hierarchical_data(form_data)
            if not is_valid:
                with st.expander("⚠️ Validation Issues", expanded=False):
                    for error in errors[:5]:  # Show first 5 errors
                        st.warning(error)
                    if len(errors) > 5:
                        st.info(f"... and {len(errors) - 5} more validation issues")
        
        # Store form data in session state
        st.session_state.form_data = form_data
    
    with tab2:
        st.subheader("XML Preview")
        
        if hasattr(st.session_state, 'form_data') and st.session_state.form_data:
            try:
                # Generate XML directly from form data to avoid Pydantic conversion issues
                st.session_state.generated_xml = st.session_state.xml_engine.generate_xml_from_form_data(
                    st.session_state.form_data
                )
                
                # Show preview (first 1000 characters)
                xml_preview = st.session_state.generated_xml
                if len(xml_preview) > 1000:
                    xml_preview = xml_preview[:1000] + "..."
                
                st.code(xml_preview, language='xml')
                
            except Exception as e:
                st.error(f"Error generating XML preview: {str(e)}")
        else:
            st.info("Fill out the form in the Data Entry tab to see XML preview")
    
    with tab3:
        st.subheader("Validation")
        
        if hasattr(st.session_state, 'generated_xml'):
            # Validate XML
            is_valid, errors = st.session_state.xml_engine.validate_xml(st.session_state.generated_xml)
            
            if is_valid:
                st.success("✅ XML is valid according to the schema!")
            else:
                st.error("❌ XML validation failed:")
                for error in errors:
                    st.error(f"• {error}")
        else:
            st.info("Generate XML in the Preview tab to validate it")
    
    with tab4:
        st.subheader("Export XML")
        
        if hasattr(st.session_state, 'generated_xml'):
            # Show export options
            col1, col2 = st.columns(2)
            
            with col1:
                # Download button
                st.download_button(
                    label="📥 Download XML",
                    data=st.session_state.generated_xml,
                    file_name=f"generated_xml_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
                    mime="application/xml"
                )
            
            with col2:
                # Copy to clipboard button
                if st.button("📋 Copy to Clipboard"):
                    st.code(st.session_state.generated_xml, language='xml')
                    st.success("XML copied to display - you can select and copy it manually")
            
            # Show file info
            st.subheader("File Information")
            xml_size = len(st.session_state.generated_xml.encode('utf-8'))
            st.info(f"XML Size: {xml_size} bytes")
            
            # Show validation status
            if hasattr(st.session_state, 'generated_xml'):
                try:
                    is_valid, errors = st.session_state.xml_engine.validate_xml(st.session_state.generated_xml)
                    
                    if is_valid:
                        st.success("✅ Ready for export - XML is valid")
                    else:
                        st.warning("⚠️ XML has validation errors - check the Validation tab")
                        
                except Exception as e:
                    st.error(f"Error validating for export: {str(e)}")
        else:
            st.info("Generate XML in the Preview tab to export it")
    
    # Footer
    st.markdown("---")
    st.markdown("🚀 Built with Streamlit • 🔧 Powered by Python • 📋 Dynamic XSD Processing")


if __name__ == "__main__":
    main()