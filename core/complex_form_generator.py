"""
Enhanced Form Generator Module
Handles complex elements (containers) vs simple elements (data holders) with 
support for optional complex elements that can be included/excluded.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Type, Set
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

from .xsd_parser import XSDParser, SchemaField
from .data_model import DataModelGenerator
from .form_generator import FormGenerator


class ComplexFormGenerator:
    """Enhanced form generator that handles complex element hierarchies"""
    
    def __init__(self, xsd_parser: XSDParser, data_model_generator: DataModelGenerator):
        self.xsd_parser = xsd_parser
        self.data_model_generator = data_model_generator
        self.base_form_generator = FormGenerator(data_model_generator)
        
        # Track which optional complex elements are included
        self.included_complex_elements: Set[str] = set()
        
        # Initialize session state for complex element toggles
        if 'complex_element_states' not in st.session_state:
            st.session_state.complex_element_states = {}
    
    def generate_hierarchical_form(self, root_field: SchemaField) -> Dict[str, Any]:
        """Generate a hierarchical form based on the XSD structure"""
        form_data = {}
        
        st.subheader(f"📋 {root_field.name} Information")
        
        if root_field.children:
            for child in root_field.children:
                child_data = self._process_field(child)
                if child_data is not None:
                    form_data[child.name] = child_data
        
        return form_data
    
    def _process_field(self, field: SchemaField, level: int = 0) -> Any:
        """Process a field - either simple or complex"""
        indent = "  " * level
        
        if field.is_complex:
            return self._process_complex_field(field, level)
        else:
            return self._process_simple_field(field, level)
    
    def _process_complex_field(self, field: SchemaField, level: int) -> Optional[Dict[str, Any]]:
        """Process a complex field (container)"""
        field_path = f"{field.parent_path}.{field.name}" if field.parent_path else field.name
        
        # Create a unique key for this complex element
        toggle_key = f"include_{field_path}_{level}"
        
        if field.required:
            # Mandatory complex element - always include
            self._render_complex_element_header(field, level, is_optional=False)
            return self._render_complex_element_children(field, level)
        else:
            # Optional complex element - show toggle
            include_element = self._render_optional_complex_element_toggle(field, level, toggle_key)
            
            if include_element:
                return self._render_complex_element_children(field, level)
            else:
                return None
    
    def _render_complex_element_header(self, field: SchemaField, level: int, is_optional: bool):
        """Render header for a complex element"""
        indent = "  " * level
        
        if level == 0:
            st.subheader(f"📦 {field.name}")
        else:
            st.markdown(f"**{indent}📦 {field.name}**")
        
        if field.documentation:
            st.markdown(f"{indent}*{field.documentation}*")
        
        if not is_optional:
            st.markdown(f"{indent}⚠️ *This section is required*")
    
    def _render_optional_complex_element_toggle(self, field: SchemaField, level: int, toggle_key: str) -> bool:
        """Render toggle for optional complex element"""
        indent = "  " * level
        
        # Get current state
        current_state = st.session_state.complex_element_states.get(toggle_key, False)
        
        # Create the toggle
        with st.container():
            col1, col2 = st.columns([1, 4])
            
            with col1:
                include_element = st.checkbox(
                    "Include",
                    value=current_state,
                    key=toggle_key,
                    help=f"Include {field.name} section in the form"
                )
            
            with col2:
                if level == 0:
                    st.subheader(f"📦 {field.name} (Optional)")
                else:
                    st.markdown(f"**{indent}📦 {field.name} (Optional)**")
                
                if field.documentation:
                    st.markdown(f"{indent}*{field.documentation}*")
        
        # Update session state
        st.session_state.complex_element_states[toggle_key] = include_element
        
        return include_element
    
    def _render_complex_element_children(self, field: SchemaField, level: int) -> Dict[str, Any]:
        """Render children of a complex element"""
        children_data = {}
        
        if field.children:
            # Group children by type for better organization
            simple_children = [child for child in field.children if not child.is_complex]
            complex_children = [child for child in field.children if child.is_complex]
            
            # Render simple children first
            if simple_children:
                for child in simple_children:
                    child_data = self._process_simple_field(child, level + 1)
                    if child_data is not None:
                        children_data[child.name] = child_data
            
            # Then render complex children
            if complex_children:
                for child in complex_children:
                    child_data = self._process_complex_field(child, level + 1)
                    if child_data is not None:
                        children_data[child.name] = child_data
        
        return children_data
    
    def _process_simple_field(self, field: SchemaField, level: int) -> Any:
        """Process a simple field (data holder)"""
        # Create field info dictionary for the base form generator
        field_info = {
            'name': field.name,
            'type': self._get_field_type(field),
            'required': field.required,
            'description': field.documentation,
            'default': None,
            'constraints': self._get_field_constraints(field)
        }
        
        # Use base form generator to create the widget
        widget_key = f"{field.parent_path}_{field.name}" if field.parent_path else field.name
        
        # Add indentation for nested fields
        if level > 0:
            indent = "  " * level
            st.markdown(f"{indent}*Field: {field.name}*")
        
        return self.base_form_generator._create_widget(field.name, field_info, widget_key)
    
    def _get_field_type(self, field: SchemaField) -> Type:
        """Get the Python type for a field"""
        # Handle enumerations
        if field.constraints and field.constraints.enumeration:
            from typing import Literal
            return Literal[tuple(field.constraints.enumeration)]
        
        # Default to string for XSD compatibility
        return str
    
    def _get_field_constraints(self, field: SchemaField) -> Dict[str, Any]:
        """Convert field constraints to dictionary format"""
        constraints = {}
        
        if field.constraints:
            if field.constraints.min_length is not None:
                constraints['min_length'] = field.constraints.min_length
            if field.constraints.max_length is not None:
                constraints['max_length'] = field.constraints.max_length
            if field.constraints.min_value is not None:
                constraints['min_value'] = field.constraints.min_value
            if field.constraints.max_value is not None:
                constraints['max_value'] = field.constraints.max_value
            if field.constraints.pattern is not None:
                constraints['pattern'] = field.constraints.pattern
            if field.constraints.enumeration is not None:
                constraints['enumeration'] = field.constraints.enumeration
        
        return constraints
    
    def create_complex_form_sections(self) -> Dict[str, Any]:
        """Create form sections organized by complex elements"""
        if not self.xsd_parser.parsed_structure:
            return {}
        
        st.title("📋 Dynamic XML Data Entry Form")
        st.markdown("*Fill out the sections below. Optional sections can be included or excluded as needed.*")
        
        # Get the root structure
        root_structure = self.xsd_parser.parsed_structure
        
        # Generate the hierarchical form
        form_data = self.generate_hierarchical_form(root_structure)
        
        return form_data
    
    def get_form_completion_stats(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about form completion"""
        def count_fields(data, is_filled_func):
            total = 0
            filled = 0
            
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict):
                        sub_total, sub_filled = count_fields(value, is_filled_func)
                        total += sub_total
                        filled += sub_filled
                    else:
                        total += 1
                        if is_filled_func(value):
                            filled += 1
            
            return total, filled
        
        def is_field_filled(value):
            return value is not None and str(value).strip() != ""
        
        total_fields, filled_fields = count_fields(form_data, is_field_filled)
        
        return {
            'total_fields': total_fields,
            'filled_fields': filled_fields,
            'completion_percentage': (filled_fields / total_fields * 100) if total_fields > 0 else 0,
            'remaining_fields': total_fields - filled_fields
        }
    
    def validate_hierarchical_data(self, form_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate hierarchical form data"""
        errors = []
        
        def validate_required_fields(data: Dict[str, Any], path: str = ""):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                
                # Find the corresponding field in the schema
                field = self._find_field_by_path(current_path)
                
                if field and field.required:
                    if isinstance(value, dict):
                        # Complex field - validate children
                        validate_required_fields(value, current_path)
                    else:
                        # Simple field - check if filled
                        if value is None or str(value).strip() == "":
                            errors.append(f"Required field '{current_path}' is empty")
        
        validate_required_fields(form_data)
        
        return len(errors) == 0, errors
    
    def _find_field_by_path(self, path: str) -> Optional[SchemaField]:
        """Find a field by its path in the schema"""
        if not self.xsd_parser.parsed_structure:
            return None
        
        parts = path.split('.')
        current = self.xsd_parser.parsed_structure
        
        for part in parts[1:]:  # Skip root element
            if not current.children:
                return None
            
            found = False
            for child in current.children:
                if child.name == part:
                    current = child
                    found = True
                    break
            
            if not found:
                return None
        
        return current