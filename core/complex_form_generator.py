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
        
        # Initialize session state for repeatable element instances
        if 'repeatable_instances' not in st.session_state:
            st.session_state.repeatable_instances = {}
    
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
    
    def _process_field(self, field: SchemaField, level: int = 0, key_prefix: str = "") -> Any:
        """Process a field - either simple or complex, handling repeatability"""
        
        # Check if this is a repeatable element
        if self._is_repeatable_element(field):
            return self._process_repeatable_field(field, level, key_prefix)
        else:
            # Non-repeatable field - process normally
            if field.is_complex:
                return self._process_complex_field(field, level, key_prefix)
            else:
                return self._process_simple_field(field, level, key_prefix)
    
    def _process_complex_field(self, field: SchemaField, level: int, key_prefix: str = "") -> Optional[Dict[str, Any]]:
        """Process a complex field (container)"""
        field_path = f"{field.parent_path}.{field.name}" if field.parent_path else field.name
        
        # Create a unique key for this complex element
        # Replace dots with underscores to create valid key names
        safe_field_path = field_path.replace('.', '_')
        toggle_key = f"include_{safe_field_path}_{level}"
        if key_prefix:
            toggle_key = f"{key_prefix}_{toggle_key}"
        
        if field.required:
            # Mandatory complex element - always include
            self._render_complex_element_header(field, level, is_optional=False)
            return self._render_complex_element_children(field, level, key_prefix)
        else:
            # Optional complex element - show toggle
            include_element = self._render_optional_complex_element_toggle(field, level, toggle_key)
            
            if include_element:
                return self._render_complex_element_children(field, level, key_prefix)
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
    
    def _render_complex_element_children(self, field: SchemaField, level: int, key_prefix: str = "") -> Dict[str, Any]:
        """Render children of a complex element"""
        children_data = {}
        
        # Store the current instance data for child processing
        saved_instance_data = getattr(self, 'current_instance_data', {})
        
        if field.children:
            # Group children by type for better organization
            simple_children = [child for child in field.children if not child.is_complex and not self._is_repeatable_element(child)]
            complex_children = [child for child in field.children if child.is_complex and not self._is_repeatable_element(child)]
            repeatable_children = [child for child in field.children if self._is_repeatable_element(child)]
            
            # Render simple children first
            if simple_children:
                for child in simple_children:
                    child_data = self._process_simple_field(child, level + 1, key_prefix)
                    if child_data is not None:
                        children_data[child.name] = child_data
            
            # Then render complex children
            if complex_children:
                for child in complex_children:
                    child_data = self._process_complex_field(child, level + 1, key_prefix)
                    if child_data is not None:
                        children_data[child.name] = child_data
            
            # Finally render repeatable children
            if repeatable_children:
                for child in repeatable_children:
                    child_data = self._process_repeatable_field(child, level + 1, key_prefix)
                    if child_data is not None:
                        children_data[child.name] = child_data
        
        # Restore the instance data context
        self.current_instance_data = saved_instance_data
        
        return children_data
    
    def _process_simple_field(self, field: SchemaField, level: int, key_prefix: str = "") -> Any:
        """Process a simple field (data holder)"""
        # Get pre-populated value if available
        default_value = None
        
        # First check if we have instance-specific data (for repeatable elements)
        if hasattr(self, 'current_instance_data') and self.current_instance_data:
            default_value = self._get_nested_value(self.current_instance_data, field.name)
        
        # If not found in instance data, check general pre-populated data
        if default_value is None and hasattr(self, 'pre_populated_data') and self.pre_populated_data:
            # Try to find the value in the pre-populated data
            default_value = self._get_nested_value(self.pre_populated_data, field.name)
        
        # Create field info dictionary for the base form generator
        field_info = {
            'name': field.name,
            'type': self._get_field_type(field),
            'required': field.required,
            'description': field.documentation,
            'default': default_value,
            'constraints': self._get_field_constraints(field)
        }
        
        # Create unique widget key with optional prefix for repeatable elements
        # Replace dots with underscores to create valid key names
        safe_parent_path = field.parent_path.replace('.', '_') if field.parent_path else ""
        base_key = f"{safe_parent_path}_{field.name}" if safe_parent_path else field.name
        widget_key = f"{key_prefix}_{base_key}" if key_prefix else base_key
        
        # Set session state with pre-populated value only if key doesn't exist
        if default_value is not None and default_value != "" and widget_key not in st.session_state:
            st.session_state[widget_key] = str(default_value) if field_info['type'] == str else default_value
        
        # Create the widget directly without extra field label
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
    
    def _get_nested_value(self, data: Dict[str, Any], field_name: str) -> Any:
        """Get a value from nested data structure, searching recursively"""
        if not isinstance(data, dict):
            return None
        
        # First, try direct lookup
        if field_name in data:
            return data[field_name]
        
        # Then search recursively in nested dictionaries
        for key, value in data.items():
            if isinstance(value, dict):
                nested_result = self._get_nested_value(value, field_name)
                if nested_result is not None:
                    return nested_result
            elif isinstance(value, list):
                # Search in list items if they are dictionaries
                for item in value:
                    if isinstance(item, dict):
                        nested_result = self._get_nested_value(item, field_name)
                        if nested_result is not None:
                            return nested_result
        
        return None
    
    def create_complex_form_sections(self, pre_populated_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create form sections organized by complex elements"""
        if not self.xsd_parser.parsed_structure:
            return {}
        
        st.title("📋 Dynamic XML Data Entry Form")
        st.markdown("*Fill out the sections below. Optional sections can be included or excluded as needed.*")
        
        # Store pre-populated data for use in form generation
        self.pre_populated_data = pre_populated_data or {}
        self.current_instance_data = {}  # Track instance-specific data
        
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
                
                if field:
                    # Only validate if field is truly required (minOccurs > 0)
                    if field.required:
                        if isinstance(value, dict):
                            # Complex field - validate children
                            validate_required_fields(value, current_path)
                        elif isinstance(value, list):
                            # List field - check if minimum occurrences are met
                            if len(value) < field.min_occurs:
                                errors.append(f"Required field '{current_path}' needs at least {field.min_occurs} items, but has {len(value)}")
                        else:
                            # Simple field - check if filled
                            if value is None or str(value).strip() == "":
                                errors.append(f"Required field '{current_path}' is empty")
                    else:
                        # Optional field - only validate children if present
                        if isinstance(value, dict) and value:
                            validate_required_fields(value, current_path)
        
        validate_required_fields(form_data)
        
        return len(errors) == 0, errors
    
    def _find_field_by_path(self, path: str) -> Optional[SchemaField]:
        """Find a field by its path in the schema"""
        if not self.xsd_parser.parsed_structure:
            return None
        
        parts = path.split('.')
        current = self.xsd_parser.parsed_structure
        
        # For single-part paths (top-level fields), look in the root's children
        if len(parts) == 1:
            if current.children:
                for child in current.children:
                    if child.name == parts[0]:
                        return child
            return None
        
        # For multi-part paths, navigate through the hierarchy
        # Skip the first part as it's typically the root element name
        for part in parts[1:]:
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
    
    def _is_repeatable_element(self, field: SchemaField) -> bool:
        """Check if an element is repeatable (maxOccurs > 1 or unbounded)"""
        return field.max_occurs is None or (field.max_occurs and field.max_occurs > 1)
    
    def _get_repeatable_instance_count(self, field_path: str) -> int:
        """Get the current number of instances for a repeatable element"""
        return st.session_state.repeatable_instances.get(field_path, 0)
    
    def _set_repeatable_instance_count(self, field_path: str, count: int):
        """Set the number of instances for a repeatable element"""
        st.session_state.repeatable_instances[field_path] = count
    
    def _get_minimum_instances(self, field: SchemaField) -> int:
        """Get the minimum number of instances required for a repeatable element"""
        return max(field.min_occurs, 0)
    
    def _initialize_repeatable_instances(self, field: SchemaField, field_path: str):
        """Initialize instances for a repeatable element if not already set"""
        if field_path not in st.session_state.repeatable_instances:
            # Start with minimum required instances, but at least 1 if min_occurs > 0
            min_instances = self._get_minimum_instances(field)
            initial_count = max(min_instances, 1) if field.required else min_instances
            self._set_repeatable_instance_count(field_path, initial_count)
    
    def _process_repeatable_field(self, field: SchemaField, level: int, key_prefix: Optional[str] = None) -> List[Any]:
        """Process a repeatable field (maxOccurs > 1)"""
        # Create a unique field path that includes the key prefix context
        base_field_path = f"{field.parent_path}.{field.name}" if field.parent_path else field.name
        field_path = f"{key_prefix}.{base_field_path}" if key_prefix else base_field_path
        indent = "  " * level
        
        # Initialize instances if needed (use base field path for session state)
        self._initialize_repeatable_instances(field, base_field_path)
        
        # Get current instance count
        instance_count = self._get_repeatable_instance_count(base_field_path)
        min_instances = self._get_minimum_instances(field)
        
        # Create header for repeatable section
        if level == 0:
            st.subheader(f"📋 {field.name} (Repeatable)")
        else:
            st.markdown(f"**{indent}📋 {field.name} (Repeatable)**")
        
        if field.documentation:
            st.markdown(f"{indent}*{field.documentation}*")
        
        # Show occurrence info
        max_text = "unlimited" if field.max_occurs is None else str(field.max_occurs)
        st.markdown(f"{indent}*Can have {field.min_occurs} to {max_text} instances*")
        
        # Add/Remove controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**Current instances: {instance_count}**")
        
        with col2:
            # Add button
            # Replace dots with underscores to create valid key names
            safe_field_path = field_path.replace('.', '_')
            add_key = f"add_{safe_field_path}_{level}"
            if st.button(f"➕ Add {field.name}", key=add_key):
                new_count = instance_count + 1
                # Check max limit
                if field.max_occurs is None or new_count <= field.max_occurs:
                    self._set_repeatable_instance_count(base_field_path, new_count)
                    st.rerun()
                else:
                    st.warning(f"Maximum {field.max_occurs} instances allowed")
        
        with col3:
            # Remove button
            # Replace dots with underscores to create valid key names
            safe_field_path = field_path.replace('.', '_')
            remove_key = f"remove_{safe_field_path}_{level}"
            if st.button(f"➖ Remove", key=remove_key):
                if instance_count > min_instances:
                    new_count = instance_count - 1
                    self._set_repeatable_instance_count(base_field_path, new_count)
                    st.rerun()
                else:
                    st.warning(f"Minimum {min_instances} instances required")
        
        # Render instances
        instances_data = []
        
        # Get pre-populated data for this field if available
        pre_populated_list = None
        if hasattr(self, 'pre_populated_data') and self.pre_populated_data:
            pre_populated_list = self._get_nested_value(self.pre_populated_data, field.name)
            if pre_populated_list and not isinstance(pre_populated_list, list):
                pre_populated_list = [pre_populated_list]  # Convert single item to list
        
        for i in range(instance_count):
            st.markdown("---")
            
            # Instance header
            if level == 0:
                st.subheader(f"📄 {field.name} #{i+1}")
            else:
                st.markdown(f"**{indent}📄 {field.name} #{i+1}**")
            
            # Create unique keys for this instance
            # Replace dots with underscores to create valid key names
            safe_field_path = field_path.replace('.', '_')
            instance_key_prefix = f"{safe_field_path}_instance_{i}"
            if key_prefix:
                instance_key_prefix = f"{key_prefix}_{instance_key_prefix}"
            
            # Set instance-specific data if available
            if pre_populated_list and i < len(pre_populated_list):
                self.current_instance_data = pre_populated_list[i] if isinstance(pre_populated_list[i], dict) else {field.name: pre_populated_list[i]}
            else:
                self.current_instance_data = {}
            
            # Process the field content for this instance
            if field.is_complex:
                # Complex repeatable element
                instance_data = self._render_complex_element_children(field, level + 1, instance_key_prefix)
            else:
                # Simple repeatable element (rare case)
                instance_data = self._process_simple_field(field, level + 1, instance_key_prefix)
            
            instances_data.append(instance_data)
        
        # Clear instance data after processing
        self.current_instance_data = {}
        
        return instances_data