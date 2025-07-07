"""
Form Generator Module
Creates dynamic Streamlit forms from Pydantic models.
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Type, Union
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal

from .data_model import DataModelGenerator
from .xsd_parser import DataType, SchemaField


class FormGenerator:
    """Generates Streamlit forms from Pydantic models"""
    
    def __init__(self, data_model_generator: DataModelGenerator):
        self.data_model_generator = data_model_generator
        self.form_data = {}
    
    def generate_form(self, model_class: Type[BaseModel], key_prefix: str = "") -> Dict[str, Any]:
        """Generate a Streamlit form for a Pydantic model"""
        form_data = {}
        
        # Get field information
        fields_info = self.data_model_generator.get_model_fields_info(model_class)
        
        # Create form sections
        st.subheader(f"{model_class.__name__} Information")
        
        for field_name, field_info in fields_info.items():
            widget_key = f"{key_prefix}_{field_name}" if key_prefix else field_name
            
            # Create appropriate widget based on field type
            value = self._create_widget(field_name, field_info, widget_key)
            form_data[field_name] = value
        
        return form_data
    
    def _create_widget(self, field_name: str, field_info: Dict[str, Any], widget_key: str) -> Any:
        """Create appropriate Streamlit widget for a field"""
        field_type = field_info['type']
        required = field_info['required']
        description = field_info.get('description') or ''
        default = field_info.get('default')
        constraints = field_info.get('constraints', {})
        
        # Handle PydanticUndefined defaults, but preserve None if it was explicitly set
        from pydantic_core import PydanticUndefined
        if default is PydanticUndefined:
            default = self._create_default_value(field_type, constraints)
        elif default is None:
            # Only create fallback default if no explicit None was provided
            if 'default' not in field_info:
                default = self._create_default_value(field_type, constraints)
        
        # Create label with required indicator
        label = field_name.replace('_', ' ').title()
        if required:
            label += " *"
        
        # Create comprehensive help text
        help_text = self._create_help_text(field_info, description)
        
        # Handle different field types
        if field_type == str:
            return self._create_text_input(label, widget_key, default, constraints, help_text, field_name)
        
        elif field_type == int:
            return self._create_number_input(label, widget_key, default, constraints, help_text, int)
        
        elif field_type in [float, Decimal]:
            return self._create_number_input(label, widget_key, default, constraints, help_text, float)
        
        elif field_type == bool:
            # Set session state value before widget creation if we have a default
            if default is not None and widget_key not in st.session_state:
                st.session_state[widget_key] = default
            return st.checkbox(label, key=widget_key, help=help_text)
        
        elif field_type == date:
            # Set session state value before widget creation if we have a default
            if default is not None and widget_key not in st.session_state:
                st.session_state[widget_key] = default
            return st.date_input(label, key=widget_key, help=help_text)
        
        elif field_type == datetime:
            # Set session state value before widget creation if we have a default
            if default is not None and widget_key not in st.session_state:
                st.session_state[widget_key] = default
            return st.datetime_input(label, key=widget_key, help=help_text)
        
        elif hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
            # Handle Optional types
            args = field_type.__args__
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
                return self._create_optional_widget(label, widget_key, non_none_type, default, constraints, help_text)
        
        elif hasattr(field_type, '__origin__'):
            # Handle Literal types (enumerations)
            from typing import Literal
            if field_type.__origin__ is Literal:
                options = list(field_type.__args__)
                
                # For optional fields, add a blank option at the beginning
                if not required:
                    options = [""] + options
                
                # Set session state value before widget creation if we have a default
                if default is not None and widget_key not in st.session_state:
                    st.session_state[widget_key] = default
                elif not required and widget_key not in st.session_state:
                    # For optional fields without default, start with blank
                    st.session_state[widget_key] = ""
                
                return st.selectbox(label, options, key=widget_key, help=help_text)
        
        elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # Handle nested models
            st.subheader(f"{label} Details")
            return self.generate_form(field_type, widget_key)
        
        # Default to text input
        return self._create_text_input(label, widget_key, default, constraints, help_text, field_name)
    
    def _create_help_text(self, field_info: Dict[str, Any], description: str) -> str:
        """Create comprehensive help text for a field"""
        help_parts = []
        
        # Add XSD element documentation if available
        xsd_documentation = self._get_xsd_documentation_for_field(field_info['name'])
        if xsd_documentation and xsd_documentation.strip():
            help_parts.append(xsd_documentation.strip())
        
        # Add description if available and different from XSD documentation
        if description and description.strip():
            description_text = description.strip()
            # Only add if it's different from XSD documentation
            if not xsd_documentation or description_text != xsd_documentation.strip():
                help_parts.append(description_text)
        
        # Add data type information - prefer XSD type over Python type
        field_type = field_info['type']
        
        # First try to get XSD data type from schema
        xsd_type_name = self._get_xsd_type_name_for_field(field_info['name'])
        
        if xsd_type_name:
            # Use XSD type name for more accurate information
            help_parts.append(f"Data type: {xsd_type_name}")
        elif hasattr(field_type, '__origin__'):
            from typing import Literal
            if field_type.__origin__ is Literal:
                # Enumeration
                options = list(field_type.__args__)
                help_parts.append(f"Select one of: {', '.join(options)}")
            else:
                # Other generic type
                type_name = getattr(field_type, '__name__', str(field_type))
                help_parts.append(f"Data type: {type_name}")
        else:
            # Regular type
            type_name = getattr(field_type, '__name__', str(field_type))
            help_parts.append(f"Data type: {type_name}")
        
        # Add constraints
        constraints = field_info.get('constraints', {})
        if constraints:
            constraint_parts = []
            if 'min_length' in constraints:
                constraint_parts.append(f"Min length: {constraints['min_length']}")
            if 'max_length' in constraints:
                constraint_parts.append(f"Max length: {constraints['max_length']}")
            if 'min_value' in constraints:
                constraint_parts.append(f"Min value: {constraints['min_value']}")
            if 'max_value' in constraints:
                constraint_parts.append(f"Max value: {constraints['max_value']}")
            if 'pattern' in constraints:
                constraint_parts.append(f"Pattern: {constraints['pattern']}")
            
            if constraint_parts:
                help_parts.append("Constraints: " + ", ".join(constraint_parts))
        
        # Add required indicator
        if field_info.get('required', False):
            help_parts.append("⚠️ This field is required")
        
        return " | ".join(help_parts) if help_parts else None
    
    def _get_xsd_type_name_for_field(self, field_name: str) -> Optional[str]:
        """Get the XSD type name for a field"""
        # Find the field in the XSD schema
        all_fields = self.data_model_generator.xsd_parser.get_all_fields()
        for field in all_fields:
            if field.name == field_name:
                # Convert DataType enum to human-readable string
                data_type = field.data_type
                type_mapping = {
                    'DataType.STRING': 'string',
                    'DataType.INTEGER': 'integer',
                    'DataType.DECIMAL': 'decimal',
                    'DataType.BOOLEAN': 'boolean',
                    'DataType.DATE': 'date',
                    'DataType.DATETIME': 'datetime',
                    'DataType.ENUMERATION': 'enumeration',
                    'DataType.LIST': 'list'
                }
                return type_mapping.get(str(data_type), str(data_type))
        
        return None
    
    def _get_xsd_documentation_for_field(self, field_name: str) -> Optional[str]:
        """Get the XSD documentation for a field"""
        # Find the field in the XSD schema
        all_fields = self.data_model_generator.xsd_parser.get_all_fields()
        for field in all_fields:
            if field.name == field_name:
                return field.documentation
        
        return None
    
    def _create_default_value(self, field_type: Type, constraints: Dict[str, Any]) -> Any:
        """Create a meaningful default value based on field type and constraints"""
        # Handle enumerations - use first option
        if hasattr(field_type, '__origin__'):
            from typing import Literal
            if field_type.__origin__ is Literal:
                return field_type.__args__[0] if field_type.__args__ else ""
        
        # Handle regular types with meaningful defaults
        if field_type == str:
            return ""  # Empty string for text fields - placeholder will show guidance
        elif field_type == int:
            if 'min_value' in constraints:
                return constraints['min_value']
            return 0
        elif field_type == float:
            if 'min_value' in constraints:
                return float(constraints['min_value'])
            return 0.0
        elif field_type == bool:
            return False
        else:
            return ""
    
    def _create_placeholder_text(self, constraints: Dict[str, Any], field_name: str = "", xsd_type: str = "") -> str:
        """Create dynamic placeholder text based on field constraints and data type"""
        # Get XSD type if not provided
        if not xsd_type and field_name:
            xsd_type = self._get_xsd_type_name_for_field(field_name)
        
        # Base text based on data type
        if xsd_type == 'date':
            base_text = "Enter date (YYYY-MM-DD)"
        elif xsd_type == 'datetime':
            base_text = "Enter datetime (YYYY-MM-DD HH:MM:SS)"
        elif xsd_type == 'integer':
            base_text = "Enter integer"
        elif xsd_type == 'decimal':
            base_text = "Enter decimal number"
        elif xsd_type == 'boolean':
            base_text = "Select true/false"
        elif xsd_type == 'enumeration':
            base_text = "Select from dropdown"
        else:
            base_text = "Enter text"
        
        # Add constraint information
        constraint_parts = []
        
        # Length constraints (for strings)
        if xsd_type in ['string', ''] or not xsd_type:
            if 'min_length' in constraints and 'max_length' in constraints:
                constraint_parts.append(f"{constraints['min_length']}-{constraints['max_length']} characters")
            elif 'max_length' in constraints:
                constraint_parts.append(f"up to {constraints['max_length']} characters")
            elif 'min_length' in constraints:
                constraint_parts.append(f"at least {constraints['min_length']} characters")
        
        # Numeric constraints (for integers/decimals)
        if xsd_type in ['integer', 'decimal']:
            if 'min_value' in constraints and 'max_value' in constraints:
                constraint_parts.append(f"between {constraints['min_value']} and {constraints['max_value']}")
            elif 'min_value' in constraints:
                constraint_parts.append(f"minimum {constraints['min_value']}")
            elif 'max_value' in constraints:
                constraint_parts.append(f"maximum {constraints['max_value']}")
        
        # Date constraints
        if xsd_type in ['date', 'datetime']:
            if 'min_value' in constraints:
                constraint_parts.append(f"from {constraints['min_value']}")
            if 'max_value' in constraints:
                constraint_parts.append(f"until {constraints['max_value']}")
        
        # Pattern constraints
        if 'pattern' in constraints:
            constraint_parts.append(f"pattern: {constraints['pattern']}")
        
        # Enumeration info (though this should be in dropdown)
        if 'enumeration' in constraints:
            options = constraints['enumeration']
            if len(options) <= 3:
                constraint_parts.append(f"({'/'.join(options)})")
            else:
                constraint_parts.append(f"({len(options)} options)")
        
        # Combine base text with constraints
        if constraint_parts:
            return f"{base_text} ({', '.join(constraint_parts)})"
        else:
            return base_text
    
    def _create_text_input(self, label: str, key: str, default: Any, constraints: Dict, help_text: Optional[str], field_name: str = "") -> str:
        """Create a text input widget with validation"""
        max_chars = constraints.get('max_length')
        
        # Create meaningful placeholder text with field name for type detection
        placeholder = self._create_placeholder_text(constraints, field_name)
        
        # Set session state value before widget creation if we have a default
        if default is not None and default != "" and key not in st.session_state:
            st.session_state[key] = str(default)
        
        if max_chars and max_chars > 100:
            # Use text area for long text
            return st.text_area(
                label,
                key=key,
                help=help_text,
                max_chars=max_chars,
                placeholder=placeholder
            )
        else:
            return st.text_input(
                label,
                key=key,
                help=help_text,
                max_chars=max_chars,
                placeholder=placeholder
            )
    
    def _create_number_input(self, label: str, key: str, default: Any, constraints: Dict, help_text: Optional[str], number_type: Type) -> Union[int, float]:
        """Create a number input widget with validation"""
        min_value = constraints.get('min_value')
        max_value = constraints.get('max_value')
        
        # Set session state value before widget creation if we have a default
        if default is not None and key not in st.session_state:
            st.session_state[key] = default
        
        if number_type == int:
            return st.number_input(
                label,
                min_value=min_value,
                max_value=max_value,
                step=1,
                key=key,
                help=help_text
            )
        else:
            return st.number_input(
                label,
                min_value=min_value,
                max_value=max_value,
                step=0.01,
                key=key,
                help=help_text
            )
    
    def _create_optional_widget(self, label: str, key: str, field_type: Type, default: Any, constraints: Dict, help_text: Optional[str]) -> Any:
        """Create widget for optional fields"""
        # Add checkbox to enable/disable the field
        enabled_key = f"{key}_enabled"
        enabled = st.checkbox(f"Include {label}", value=default is not None, key=enabled_key)
        
        if enabled:
            # Create the actual widget
            temp_field_info = {
                'type': field_type,
                'required': False,
                'description': help_text,
                'default': default,
                'constraints': constraints
            }
            return self._create_widget(label, temp_field_info, key)
        else:
            return None
    
    def validate_form_data(self, form_data: Dict[str, Any], model_class: Type[BaseModel]) -> tuple[bool, List[str]]:
        """Validate form data against the model"""
        errors = []
        
        try:
            # Try to create model instance
            model_instance = model_class(**form_data)
            return True, []
        except Exception as e:
            # Handle Pydantic validation errors
            if hasattr(e, 'errors'):
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error.get('loc', []))
                    msg = error.get('msg', str(error))
                    errors.append(f"{field}: {msg}")
            else:
                errors.append(str(e))
            return False, errors
    
    def display_validation_errors(self, errors: List[str]):
        """Display validation errors in Streamlit"""
        if errors:
            st.error("Please fix the following errors:")
            for error in errors:
                st.error(f"• {error}")
    
    def create_form_sections(self, model_class: Type[BaseModel]) -> Dict[str, Any]:
        """Create organized form sections"""
        form_data = {}
        
        # Get field information
        fields_info = self.data_model_generator.get_model_fields_info(model_class)
        
        # Group fields by categories (you can customize this logic)
        sections = self._group_fields_by_category(fields_info)
        
        for section_name, section_fields in sections.items():
            with st.expander(f"{section_name}", expanded=True):
                for field_name in section_fields:
                    field_info = fields_info[field_name]
                    value = self._create_widget(field_name, field_info, field_name)
                    form_data[field_name] = value
        
        return form_data
    
    def _group_fields_by_category(self, fields_info: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
        """Group fields into logical categories"""
        # Simple categorization - you can make this more sophisticated
        categories = {
            "Basic Information": [],
            "Details": [],
            "Dates & Numbers": [],
            "Other": []
        }
        
        for field_name, field_info in fields_info.items():
            field_type = field_info['type']
            
            if field_name.lower() in ['name', 'title', 'acronym', 'abstract']:
                categories["Basic Information"].append(field_name)
            elif field_type in [date, datetime, int, float, Decimal]:
                categories["Dates & Numbers"].append(field_name)
            elif len(field_info.get('description') or '') > 50:
                categories["Details"].append(field_name)
            else:
                categories["Other"].append(field_name)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def create_sidebar_form(self, model_class: Type[BaseModel]) -> Dict[str, Any]:
        """Create a form in the sidebar"""
        with st.sidebar:
            st.header("Data Entry Form")
            return self.generate_form(model_class, "sidebar")
    
    def save_form_state(self, form_data: Dict[str, Any], key: str = "form_state"):
        """Save form state to session"""
        if 'form_states' not in st.session_state:
            st.session_state.form_states = {}
        st.session_state.form_states[key] = form_data
    
    def load_form_state(self, key: str = "form_state") -> Optional[Dict[str, Any]]:
        """Load form state from session"""
        if 'form_states' in st.session_state:
            return st.session_state.form_states.get(key)
        return None