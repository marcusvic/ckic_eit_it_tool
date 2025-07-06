"""
XSD Parser Module
Dynamically parses XSD files to extract schema structure and constraints.
"""

import xmlschema
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class DataType(Enum):
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ENUMERATION = "enumeration"
    LIST = "list"


@dataclass
class FieldConstraint:
    """Represents constraints for a field"""
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    enumeration: Optional[List[str]] = None


@dataclass
class SchemaField:
    """Represents a field in the XSD schema"""
    name: str
    data_type: DataType
    required: bool
    documentation: Optional[str] = None
    constraints: Optional[FieldConstraint] = None
    children: Optional[List['SchemaField']] = None
    is_complex: bool = False  # True if this is a container element
    parent_path: str = ""     # Path to parent element


class XSDParser:
    """Parses XSD files and extracts schema information"""
    
    def __init__(self, xsd_path: str):
        self.xsd_path = xsd_path
        self.schema = xmlschema.XMLSchema(xsd_path)
        self.root_element = None
        self.parsed_structure = None
    
    def parse(self) -> Dict[str, Any]:
        """Parse the XSD file and return structured information"""
        try:
            # Get the root element
            root_elements = list(self.schema.elements.values())
            if not root_elements:
                raise ValueError("No root elements found in XSD")
            
            self.root_element = root_elements[0]
            self.parsed_structure = self._parse_element(self.root_element)
            
            return {
                "root_element": self.root_element.name,
                "structure": self.parsed_structure,
                "namespace": self.schema.target_namespace
            }
            
        except Exception as e:
            raise Exception(f"Failed to parse XSD: {str(e)}")
    
    def _parse_element(self, element, parent_path: str = "") -> SchemaField:
        """Parse an individual element and its children"""
        current_path = f"{parent_path}.{element.name}" if parent_path else element.name
        
        field = SchemaField(
            name=element.name,
            data_type=self._get_data_type(element),
            required=element.min_occurs > 0,
            documentation=self._get_documentation(element),
            constraints=self._get_constraints(element),
            parent_path=parent_path
        )
        
        # Handle complex types with children
        if hasattr(element.type, 'content') and element.type.content:
            field.is_complex = True
            field.children = self._parse_complex_type(element.type, current_path)
        
        return field
    
    def _parse_complex_type(self, complex_type, parent_path: str = "") -> List[SchemaField]:
        """Parse complex type and extract child elements"""
        children = []
        
        if hasattr(complex_type, 'content') and complex_type.content:
            for child in complex_type.content:
                if hasattr(child, 'iter_elements'):
                    for elem in child.iter_elements():
                        children.append(self._parse_element(elem, parent_path))
                elif hasattr(child, 'name'):
                    children.append(self._parse_element(child, parent_path))
        
        return children
    
    def _get_data_type(self, element) -> DataType:
        """Determine the data type of an element"""
        # First check for enumerations
        if hasattr(element.type, 'facets') and element.type.facets:
            for facet_name, facet_obj in element.type.facets.items():
                local_name = facet_name.split('}')[-1] if '}' in str(facet_name) else str(facet_name)
                if local_name == 'enumeration':
                    return DataType.ENUMERATION
        
        # Check for base type (most reliable for XSD types)
        base_type_name = ""
        if hasattr(element.type, 'base_type') and element.type.base_type:
            base_type_name = getattr(element.type.base_type, 'name', '')
            if base_type_name:
                # Extract local name from namespaced type
                base_type_name = base_type_name.split('}')[-1] if '}' in base_type_name else base_type_name
                base_type_name = base_type_name.lower()
                
                if base_type_name == 'date':
                    return DataType.DATE
                elif base_type_name == 'datetime':
                    return DataType.DATETIME
                elif base_type_name in ['int', 'integer', 'nonnegativeinteger', 'positiveinteger', 'long']:
                    return DataType.INTEGER
                elif base_type_name in ['decimal', 'double', 'float']:
                    return DataType.DECIMAL
                elif base_type_name in ['boolean', 'bool']:
                    return DataType.BOOLEAN
        
        # Check python type if available
        if hasattr(element.type, 'python_type'):
            python_type = element.type.python_type
            if python_type == str:
                return DataType.STRING
            elif python_type == int:
                return DataType.INTEGER
            elif python_type == float:
                return DataType.DECIMAL
            elif python_type == bool:
                return DataType.BOOLEAN
        
        # Check element type name
        type_name = getattr(element.type, 'name', '')
        if type_name:
            type_name = type_name.lower()
            if 'date' in type_name:
                if 'time' in type_name:
                    return DataType.DATETIME
                else:
                    return DataType.DATE
            elif 'int' in type_name or 'long' in type_name:
                return DataType.INTEGER
            elif 'decimal' in type_name or 'double' in type_name:
                return DataType.DECIMAL
            elif 'bool' in type_name:
                return DataType.BOOLEAN
        
        # Check for list types
        if hasattr(element.type, 'item_type'):
            return DataType.LIST
        
        return DataType.STRING
    
    def _get_documentation(self, element) -> Optional[str]:
        """Extract documentation from element"""
        # First check direct annotation on the element
        if hasattr(element, 'annotation') and element.annotation:
            for doc in element.annotation.documentation:
                if doc.text:
                    return doc.text.strip()
        
        # If no direct annotation, check the element's type annotation
        if hasattr(element, 'type') and hasattr(element.type, 'annotation') and element.type.annotation:
            for doc in element.type.annotation.documentation:
                if doc.text:
                    return doc.text.strip()
        
        # For complex types, check if the type has content with annotation
        if hasattr(element, 'type') and hasattr(element.type, 'content'):
            if hasattr(element.type.content, 'annotation') and element.type.content.annotation:
                for doc in element.type.content.annotation.documentation:
                    if doc.text:
                        return doc.text.strip()
        
        return None
    
    def _get_constraints(self, element) -> Optional[FieldConstraint]:
        """Extract constraints from element"""
        constraints = FieldConstraint()
        has_constraints = False
        
        # Check for facets in element type
        if hasattr(element.type, 'facets') and element.type.facets:
            for facet_name, facet_obj in element.type.facets.items():
                # Extract the local name from the namespaced facet name
                local_name = facet_name.split('}')[-1] if '}' in str(facet_name) else str(facet_name)
                
                # Get the actual value from the facet object
                facet_value = getattr(facet_obj, 'value', facet_obj)
                
                if local_name == 'minLength':
                    constraints.min_length = facet_value
                    has_constraints = True
                elif local_name == 'maxLength':
                    constraints.max_length = facet_value
                    has_constraints = True
                elif local_name == 'minInclusive':
                    constraints.min_value = facet_value
                    has_constraints = True
                elif local_name == 'maxInclusive':
                    constraints.max_value = facet_value
                    has_constraints = True
                elif local_name == 'pattern':
                    constraints.pattern = facet_value
                    has_constraints = True
                elif local_name == 'enumeration':
                    # Handle enumeration facets specially
                    if hasattr(facet_obj, '__iter__') and not isinstance(facet_obj, str):
                        constraints.enumeration = list(facet_obj)
                    else:
                        constraints.enumeration = [facet_value]
                    has_constraints = True
        
        # Check for enumeration values directly (fallback)
        if hasattr(element.type, 'enumeration') and element.type.enumeration:
            constraints.enumeration = list(element.type.enumeration)
            has_constraints = True
        
        return constraints if has_constraints else None
    
    def get_field_by_path(self, path: str) -> Optional[SchemaField]:
        """Get a field by its path (e.g., 'Project.Abstract')"""
        if not self.parsed_structure:
            return None
        
        parts = path.split('.')
        current = self.parsed_structure
        
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
    
    def get_all_fields(self) -> List[SchemaField]:
        """Get all fields in the schema as a flat list"""
        if not self.parsed_structure:
            return []
        
        fields = []
        self._collect_fields(self.parsed_structure, fields)
        return fields
    
    def _collect_fields(self, field: SchemaField, fields: List[SchemaField]):
        """Recursively collect all fields"""
        fields.append(field)
        if field.children:
            for child in field.children:
                self._collect_fields(child, fields)
    
    def get_complex_elements(self) -> List[SchemaField]:
        """Get all complex elements (containers) in the schema"""
        if not self.parsed_structure:
            return []
        
        complex_fields = []
        self._collect_complex_fields(self.parsed_structure, complex_fields)
        return complex_fields
    
    def _collect_complex_fields(self, field: SchemaField, complex_fields: List[SchemaField]):
        """Recursively collect complex fields"""
        if field.is_complex:
            complex_fields.append(field)
        if field.children:
            for child in field.children:
                self._collect_complex_fields(child, complex_fields)
    
    def get_simple_elements(self) -> List[SchemaField]:
        """Get all simple elements (data holders) in the schema"""
        if not self.parsed_structure:
            return []
        
        simple_fields = []
        self._collect_simple_fields(self.parsed_structure, simple_fields)
        return simple_fields
    
    def _collect_simple_fields(self, field: SchemaField, simple_fields: List[SchemaField]):
        """Recursively collect simple fields"""
        if not field.is_complex:
            simple_fields.append(field)
        if field.children:
            for child in field.children:
                self._collect_simple_fields(child, simple_fields)