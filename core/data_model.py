"""
Data Model Generator Module
Creates dynamic Pydantic models from XSD schema structure.
"""

from typing import Dict, List, Any, Optional, Union, Type, get_type_hints
from pydantic import BaseModel, Field, validator, create_model
from datetime import date, datetime
from decimal import Decimal
import re

from .xsd_parser import XSDParser, SchemaField, DataType, FieldConstraint


class DataModelGenerator:
    """Generates Pydantic models from XSD schema"""
    
    def __init__(self, xsd_parser: XSDParser):
        self.xsd_parser = xsd_parser
        self.models_cache: Dict[str, Type[BaseModel]] = {}
    
    def generate_models(self) -> Dict[str, Type[BaseModel]]:
        """Generate all Pydantic models from the XSD schema"""
        if not self.xsd_parser.parsed_structure:
            raise ValueError("XSD must be parsed before generating models")
        
        # Start with root model
        root_model = self._create_model_from_field(self.xsd_parser.parsed_structure)
        self.models_cache[self.xsd_parser.parsed_structure.name] = root_model
        
        return self.models_cache
    
    def _create_model_from_field(self, field: SchemaField) -> Type[BaseModel]:
        """Create a Pydantic model from a schema field"""
        if field.name in self.models_cache:
            return self.models_cache[field.name]
        
        # Create fields dictionary for the model
        fields_dict = {}
        validators_dict = {}
        
        if field.children:
            for child in field.children:
                field_type, field_info = self._get_field_type_and_info(child)
                fields_dict[child.name] = (field_type, field_info)
                
                # Add custom validators if needed
                if child.constraints:
                    validator_func = self._create_validator(child)
                    if validator_func:
                        validators_dict[f'validate_{child.name}'] = validator_func
        
        # Create the model
        model_class = create_model(
            field.name,
            **fields_dict,
            __validators__=validators_dict
        )
        
        # Cache the model
        self.models_cache[field.name] = model_class
        
        return model_class
    
    def _get_field_type_and_info(self, field: SchemaField) -> tuple:
        """Get the Python type and Field info for a schema field"""
        # Determine base type
        base_type = self._get_python_type(field)
        
        # Handle repeatable elements (maxOccurs > 1 or unbounded)
        if self._is_repeatable_element(field):
            base_type = List[base_type]
        
        # Handle optional fields
        if not field.required:
            base_type = Optional[base_type]
        
        # Create Field with constraints
        field_kwargs = {}
        
        # Add description
        if field.documentation:
            field_kwargs['description'] = field.documentation
        
        # Add constraints (with type checking for Pydantic compatibility)
        if field.constraints:
            if field.constraints.min_length is not None and isinstance(field.constraints.min_length, (int, float)):
                field_kwargs['min_length'] = field.constraints.min_length
            if field.constraints.max_length is not None and isinstance(field.constraints.max_length, (int, float)):
                field_kwargs['max_length'] = field.constraints.max_length
            
            # Only apply numeric constraints (ge/le) to numeric data types
            if field.data_type in [DataType.INTEGER, DataType.DECIMAL]:
                if field.constraints.min_value is not None and isinstance(field.constraints.min_value, (int, float)):
                    field_kwargs['ge'] = field.constraints.min_value
                if field.constraints.max_value is not None and isinstance(field.constraints.max_value, (int, float)):
                    field_kwargs['le'] = field.constraints.max_value
        
        # Set default value for optional fields
        if not field.required:
            field_kwargs['default'] = None
        
        field_info = Field(**field_kwargs)
        
        return base_type, field_info
    
    def _get_python_type(self, field: SchemaField) -> Type:
        """Convert XSD data type to Python type"""
        if field.children:
            # Complex type - create nested model
            return self._create_model_from_field(field)
        
        # Handle enumerations first
        if field.constraints and field.constraints.enumeration:
            # Create enum-like literal type
            from typing import Literal
            return Literal[tuple(field.constraints.enumeration)]
        
        # Simple types - use appropriate types for constrained fields
        if field.data_type == DataType.INTEGER:
            # Use int type if there are numeric constraints, otherwise str
            if field.constraints and (field.constraints.min_value is not None or field.constraints.max_value is not None):
                return int
            else:
                return str
        elif field.data_type == DataType.DECIMAL:
            # Use float type if there are numeric constraints, otherwise str
            if field.constraints and (field.constraints.min_value is not None or field.constraints.max_value is not None):
                return float
            else:
                return str
        else:
            # Default type mapping for other types
            type_mapping = {
                DataType.STRING: str,
                DataType.BOOLEAN: str,  # XSD booleans are often strings
                DataType.DATE: str,     # XSD dates are ISO format strings
                DataType.DATETIME: str, # XSD datetimes are ISO format strings
                DataType.LIST: List[str]
            }
            
            return type_mapping.get(field.data_type, str)
    
    def _create_validator(self, field: SchemaField):
        """Create a custom validator for a field"""
        if not field.constraints:
            return None
        
        def validator_func(cls, v):
            constraints = field.constraints
            
            # String length validation
            if isinstance(v, str):
                if constraints.min_length is not None and len(v) < constraints.min_length:
                    raise ValueError(f'{field.name} must be at least {constraints.min_length} characters long')
                if constraints.max_length is not None and len(v) > constraints.max_length:
                    raise ValueError(f'{field.name} must be at most {constraints.max_length} characters long')
            
            # Numeric range validation
            if isinstance(v, (int, float, Decimal)):
                if constraints.min_value is not None and v < constraints.min_value:
                    raise ValueError(f'{field.name} must be at least {constraints.min_value}')
                if constraints.max_value is not None and v > constraints.max_value:
                    raise ValueError(f'{field.name} must be at most {constraints.max_value}')
            
            # Pattern validation
            if constraints.pattern and isinstance(v, str):
                if not re.match(constraints.pattern, v):
                    raise ValueError(f'{field.name} does not match required pattern')
            
            # Enumeration validation
            if constraints.enumeration and v not in constraints.enumeration:
                raise ValueError(f'{field.name} must be one of: {", ".join(constraints.enumeration)}')
            
            return v
        
        return validator(field.name, allow_reuse=True)(validator_func)
    
    def create_empty_instance(self, model_class: Type[BaseModel]) -> BaseModel:
        """Create an empty instance of a model with default values"""
        # Get all fields and their default values
        field_values = {}
        
        # Use model_fields for Pydantic v2
        if hasattr(model_class, 'model_fields'):
            fields = model_class.model_fields
        else:
            # Fallback for older Pydantic versions
            fields = model_class.__fields__
        
        for field_name, field_info in fields.items():
            # Handle Pydantic v2 vs v1 differences
            if hasattr(field_info, 'annotation'):
                # Pydantic v2
                from pydantic_core import PydanticUndefined
                field_type = field_info.annotation
                required = field_info.is_required()
                default_value = field_info.default if field_info.default not in (PydanticUndefined, ...) else None
                default_factory = getattr(field_info, 'default_factory', None)
            else:
                # Pydantic v1
                field_type = getattr(field_info, 'type_', str)
                required = getattr(field_info, 'required', True)
                default_value = getattr(field_info, 'default', None)
                default_factory = getattr(field_info, 'default_factory', None)
            
            if default_value is not None:
                field_values[field_name] = default_value
            elif default_factory is not None:
                field_values[field_name] = default_factory()
            elif not required:
                field_values[field_name] = None
            else:
                # For required fields, try to set reasonable defaults
                if field_type == str:
                    field_values[field_name] = ""
                elif field_type == int:
                    field_values[field_name] = 0
                elif field_type == float:
                    field_values[field_name] = 0.0
                elif field_type == bool:
                    field_values[field_name] = False
                elif field_type == date:
                    field_values[field_name] = date.today()
                elif field_type == datetime:
                    field_values[field_name] = datetime.now()
                else:
                    # For complex types, create empty instance recursively
                    if hasattr(field_type, 'model_fields') or hasattr(field_type, '__fields__'):
                        field_values[field_name] = self.create_empty_instance(field_type)
        
        return model_class(**field_values)
    
    def get_model_fields_info(self, model_class: Type[BaseModel]) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about model fields for UI generation"""
        fields_info = {}
        
        # Use model_fields for Pydantic v2
        if hasattr(model_class, 'model_fields'):
            fields = model_class.model_fields
        else:
            # Fallback for older Pydantic versions
            fields = model_class.__fields__
        
        for field_name, field_info in fields.items():
            # Handle Pydantic v2 vs v1 differences
            if hasattr(field_info, 'annotation'):
                # Pydantic v2
                from pydantic_core import PydanticUndefined
                field_type = field_info.annotation
                required = field_info.is_required()
                default_value = field_info.default if field_info.default not in (PydanticUndefined, ...) else None
                description = field_info.description
            else:
                # Pydantic v1
                field_type = getattr(field_info, 'type_', str)
                required = getattr(field_info, 'required', True)
                default_value = getattr(field_info, 'default', None)
                description = getattr(field_info.field_info, 'description', None) if hasattr(field_info, 'field_info') else None
            
            info = {
                'name': field_name,
                'type': field_type,
                'required': required,
                'description': description,
                'default': default_value,
                'constraints': {}
            }
            
            # Extract constraints from XSD schema (our custom approach)
            # Find the corresponding schema field to get XSD constraints
            schema_field = self._find_schema_field_for_model_field(field_name)
            if schema_field and schema_field.constraints:
                xsd_constraints = schema_field.constraints
                if xsd_constraints.min_length is not None and isinstance(xsd_constraints.min_length, (int, float)):
                    info['constraints']['min_length'] = xsd_constraints.min_length
                if xsd_constraints.max_length is not None and isinstance(xsd_constraints.max_length, (int, float)):
                    info['constraints']['max_length'] = xsd_constraints.max_length
                if xsd_constraints.min_value is not None and isinstance(xsd_constraints.min_value, (int, float)):
                    info['constraints']['min_value'] = xsd_constraints.min_value
                if xsd_constraints.max_value is not None and isinstance(xsd_constraints.max_value, (int, float)):
                    info['constraints']['max_value'] = xsd_constraints.max_value
                if xsd_constraints.pattern is not None and isinstance(xsd_constraints.pattern, str):
                    info['constraints']['pattern'] = xsd_constraints.pattern
                if xsd_constraints.enumeration is not None and isinstance(xsd_constraints.enumeration, list):
                    info['constraints']['enumeration'] = xsd_constraints.enumeration
            
            # Also check Pydantic constraints (fallback)
            if hasattr(field_info, 'constraints'):
                # Pydantic v2
                constraints = field_info.constraints
                if constraints:
                    for constraint in constraints:
                        constraint_type = type(constraint).__name__
                        if 'MinLen' in constraint_type:
                            info['constraints']['min_length'] = constraint.min_length
                        elif 'MaxLen' in constraint_type:
                            info['constraints']['max_length'] = constraint.max_length
                        elif 'Ge' in constraint_type:
                            info['constraints']['min_value'] = constraint.ge
                        elif 'Le' in constraint_type:
                            info['constraints']['max_value'] = constraint.le
            elif hasattr(field_info, 'field_info'):
                # Pydantic v1
                field_info_obj = field_info.field_info
                if hasattr(field_info_obj, 'min_length'):
                    info['constraints']['min_length'] = field_info_obj.min_length
                if hasattr(field_info_obj, 'max_length'):
                    info['constraints']['max_length'] = field_info_obj.max_length
                if hasattr(field_info_obj, 'ge'):
                    info['constraints']['min_value'] = field_info_obj.ge
                if hasattr(field_info_obj, 'le'):
                    info['constraints']['max_value'] = field_info_obj.le
            
            fields_info[field_name] = info
        
        return fields_info
    
    def _find_schema_field_for_model_field(self, field_name: str) -> Optional['SchemaField']:
        """Find the corresponding schema field for a model field name"""
        if not self.xsd_parser.parsed_structure:
            return None
        
        # Search through all fields to find matching name
        all_fields = self.xsd_parser.get_all_fields()
        for field in all_fields:
            if field.name == field_name:
                return field
        
        return None
    def _is_repeatable_element(self, field: SchemaField) -> bool:
        """Check if an element is repeatable (maxOccurs > 1 or unbounded)"""
        return field.max_occurs is None or (field.max_occurs and field.max_occurs > 1)
