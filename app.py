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
from core.xml_ingestion import XMLIngestor


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
    if 'xml_ingestor' not in st.session_state:
        st.session_state.xml_ingestor = None
    if 'root_model' not in st.session_state:
        st.session_state.root_model = None
    if 'current_xsd_path' not in st.session_state:
        st.session_state.current_xsd_path = None
    if 'ingested_xml_data' not in st.session_state:
        st.session_state.ingested_xml_data = None
    if 'temp_imported_data' not in st.session_state:
        st.session_state.temp_imported_data = None


def preprocess_imported_data_for_repeatables(imported_data: Dict[str, Any], xsd_parser) -> Dict[str, Any]:
    """Preprocess imported data to handle repeatable elements correctly"""
    if not imported_data or not xsd_parser:
        return imported_data
    
    # Initialize repeatable instances in session state if not exists
    if 'repeatable_instances' not in st.session_state:
        st.session_state.repeatable_instances = {}
    
    # First pass: Find all repeatable elements in the schema and their paths
    def find_repeatable_paths(schema_field, parent_path=""):
        """Find all repeatable element paths in the schema"""
        repeatable_paths = {}
        
        if not schema_field or not hasattr(schema_field, 'children') or schema_field.children is None:
            return repeatable_paths
            
        for child in schema_field.children:
            if child is None:
                continue
                
            field_path = f"{parent_path}.{child.name}" if parent_path else child.name
            
            # Check if this field is repeatable
            if hasattr(child, 'max_occurs') and (child.max_occurs is None or child.max_occurs > 1):
                repeatable_paths[child.name] = field_path
            
            # Recursively check children if they exist
            if hasattr(child, 'children') and child.children is not None:
                child_paths = find_repeatable_paths(child, field_path)
                repeatable_paths.update(child_paths)
        
        return repeatable_paths
    
    # Get all repeatable paths from schema
    repeatable_paths = find_repeatable_paths(xsd_parser.parsed_structure)
    
    # Second pass: Process the imported data and count instances
    def count_instances_in_data(data: Dict[str, Any], parent_path: str = ""):
        """Count instances of repeatable elements in the data"""
        for key, value in data.items():
            current_path = f"{parent_path}.{key}" if parent_path else key
            
            # Check if this key corresponds to a repeatable element
            if key in repeatable_paths:
                # The schema path includes the root "Project" element, but our data doesn't
                # So we need to prepend "Project" to match the schema paths
                schema_path = repeatable_paths[key]
                if not schema_path.startswith("Project."):
                    full_path = f"Project.{schema_path}"
                else:
                    full_path = schema_path
                    
                if isinstance(value, list):
                    count = len(value)
                    st.session_state.repeatable_instances[full_path] = count
                else:
                    st.session_state.repeatable_instances[full_path] = 1
            
            # Recursively process nested dictionaries
            if isinstance(value, dict):
                count_instances_in_data(value, current_path)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        count_instances_in_data(item, current_path)
    
    # Count instances in the imported data
    count_instances_in_data(imported_data)
    
    
    return imported_data


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
        
        # Initialize XML ingestor
        xml_ingestor = XMLIngestor(xsd_parser)
        
        # Store in session state
        st.session_state.xsd_parser = xsd_parser
        st.session_state.data_model_generator = data_model_generator
        st.session_state.form_generator = form_generator
        st.session_state.complex_form_generator = complex_form_generator
        st.session_state.xml_engine = xml_engine
        st.session_state.xml_ingestor = xml_ingestor
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
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Data Entry", "📥 XML Import", "🔍 Preview", "✅ Validate", "📁 Export"])
    
    with tab1:
        st.subheader("📝 Data Entry Form")
        
        # Check if we have imported XML data to pre-populate the form
        pre_populated_data = None
        if hasattr(st.session_state, 'ingested_xml_data') and st.session_state.ingested_xml_data:
            pre_populated_data = st.session_state.ingested_xml_data
            st.info("📥 Form is pre-populated with imported XML data")
        
        # Always use hierarchical form with pre-populated data
        form_data = st.session_state.complex_form_generator.create_complex_form_sections(pre_populated_data)
        
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
        st.subheader("📥 XML Import & Population")
        
        # XML import options
        xml_import_option = st.radio(
            "Select XML source:",
            ["Upload XML file", "Paste XML content", "Use existing XML file"]
        )
        
        imported_data = None
        
        if xml_import_option == "Upload XML file":
            uploaded_xml = st.file_uploader("Upload XML file", type=['xml'])
            if uploaded_xml is not None:
                try:
                    # Read uploaded file content
                    xml_content = uploaded_xml.getvalue().decode('utf-8')
                    
                    # Parse and populate form data
                    imported_data = st.session_state.xml_ingestor.populate_form_from_xml_string(xml_content)
                    
                    st.success(f"Successfully imported XML from {uploaded_xml.name}")
                    
                except Exception as e:
                    st.error(f"Error reading XML file: {str(e)}")
        
        elif xml_import_option == "Paste XML content":
            xml_content = st.text_area("Paste XML content here:", height=200)
            if xml_content.strip():
                if st.button("Parse XML Content"):
                    try:
                        imported_data = st.session_state.xml_ingestor.populate_form_from_xml_string(xml_content)
                        st.success("Successfully parsed XML content")
                    except Exception as e:
                        st.error(f"Error parsing XML content: {str(e)}")
        
        elif xml_import_option == "Use existing XML file":
            # Look for XML files in current directory
            xml_files = [f for f in os.listdir('.') if f.endswith('.xml')]
            if xml_files:
                selected_xml = st.selectbox("Select XML file:", xml_files)
                if st.button("Load XML File"):
                    try:
                        imported_data = st.session_state.xml_ingestor.populate_form_from_xml(selected_xml)
                        st.success(f"Successfully imported XML from {selected_xml}")
                    except Exception as e:
                        st.error(f"Error loading XML file: {str(e)}")
            else:
                st.warning("No XML files found in current directory")
        
        # Display imported data and populate form
        if imported_data:
            # Store the imported data temporarily
            st.session_state.temp_imported_data = imported_data
            
            # Show XML statistics
            with st.expander("📊 XML Import Statistics", expanded=False):
                stats = st.session_state.xml_ingestor.get_xml_statistics(imported_data)
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Fields", stats['total_fields'])
                with col2:
                    st.metric("Simple Fields", stats['simple_fields'])
                with col3:
                    st.metric("Complex Fields", stats['complex_fields'])
                
                if stats['field_names']:
                    st.write("**Field Names:**")
                    st.write(", ".join(stats['field_names'][:20]))
                    if len(stats['field_names']) > 20:
                        st.write(f"... and {len(stats['field_names']) - 20} more")
            
            # Show structure preview
            with st.expander("🔍 XML Structure Preview", expanded=False):
                preview = st.session_state.xml_ingestor.preview_xml_structure(imported_data)
                st.code(preview, language='python')
            
            # Success message
            st.success("✅ XML data imported successfully!")
        
        # Show prepopulate button if we have imported data
        if hasattr(st.session_state, 'temp_imported_data') and st.session_state.temp_imported_data:
            st.info("XML data has been imported. Click the button below to prepopulate the form.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📝 Prepopulate Form", type="primary"):
                    # Preprocess the data to handle repeatable elements
                    preprocessed_data = preprocess_imported_data_for_repeatables(
                        st.session_state.temp_imported_data, 
                        st.session_state.xsd_parser
                    )
                    
                    # Move preprocessed data to ingested data
                    st.session_state.ingested_xml_data = preprocessed_data
                    st.session_state.temp_imported_data = None
                    
                    # Clear ALL form widget keys to force regeneration with new values
                    # This includes keys with underscores that represent form fields
                    keys_to_preserve = {
                        'xsd_parser', 'data_model_generator', 'form_generator', 
                        'complex_form_generator', 'xml_engine', 'xml_ingestor', 
                        'root_model', 'current_xsd_path', 'ingested_xml_data',
                        'complex_element_states', 'repeatable_instances', 'form_data',
                        'temp_imported_data'
                    }
                    
                    # Clear all keys except system keys (starting with _) and preserved keys
                    keys_to_clear = []
                    for key in list(st.session_state.keys()):
                        if not key.startswith('_') and key not in keys_to_preserve:
                            keys_to_clear.append(key)
                    
                    for key in keys_to_clear:
                        del st.session_state[key]
                    
                    st.rerun()
            
            with col2:
                if st.button("❌ Discard Import"):
                    st.session_state.temp_imported_data = None
                    st.rerun()
        
        # Show current ingested data if exists
        elif hasattr(st.session_state, 'ingested_xml_data') and st.session_state.ingested_xml_data:
            st.info("Form has been prepopulated with XML data.")
            
            # Option to clear imported data
            if st.button("🗑️ Clear Imported Data"):
                st.session_state.ingested_xml_data = None
                
                # Clear all form widget keys to reset the form
                keys_to_preserve = {
                    'xsd_parser', 'data_model_generator', 'form_generator', 
                    'complex_form_generator', 'xml_engine', 'xml_ingestor', 
                    'root_model', 'current_xsd_path', 'ingested_xml_data',
                    'complex_element_states', 'repeatable_instances', 'temp_imported_data'
                }
                
                # Clear all keys except system keys (starting with _) and preserved keys
                keys_to_clear = []
                for key in list(st.session_state.keys()):
                    if not key.startswith('_') and key not in keys_to_preserve:
                        keys_to_clear.append(key)
                
                for key in keys_to_clear:
                    del st.session_state[key]
                
                st.rerun()
    
    with tab3:
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
    
    with tab4:
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
    
    with tab5:
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