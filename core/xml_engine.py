"""
XML Generation Engine Module
Generates XML files from Pydantic models and validates against XSD.
"""

import xml.etree.ElementTree as ET
from lxml import etree
from typing import Dict, List, Any, Optional, Type, Union
from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
import xmlschema

from .xsd_parser import XSDParser, SchemaField


class XMLEngine:
    """Generates and validates XML files from Pydantic models"""
    
    def __init__(self, xsd_parser: XSDParser):
        self.xsd_parser = xsd_parser
        self.schema = xmlschema.XMLSchema(xsd_parser.xsd_path)
    
    def create_model_instance_from_form_data(self, form_data: Dict[str, Any], model_class: Type[BaseModel]) -> BaseModel:
        """Convert form data with lists of dictionaries to proper Pydantic model instance"""
        # Get model fields info
        if hasattr(model_class, 'model_fields'):
            fields = model_class.model_fields
        else:
            fields = model_class.__fields__
        
        processed_data = {}
        
        for field_name, field_value in form_data.items():
            if field_name not in fields:
                continue
            
            # Skip empty optional fields
            if field_value is None or (isinstance(field_value, str) and field_value.strip() == ""):
                field_info = fields[field_name]
                # Check if field is required
                if hasattr(field_info, 'is_required'):
                    is_required = field_info.is_required()
                else:
                    is_required = getattr(field_info, 'required', True)
                
                if not is_required:
                    # Skip optional empty fields
                    continue
                else:
                    # Set None for required empty fields (let Pydantic handle validation)
                    processed_data[field_name] = None
                    continue
                
            field_info = fields[field_name]
            
            # Get field type
            if hasattr(field_info, 'annotation'):
                field_type = field_info.annotation
            else:
                field_type = getattr(field_info, 'type_', str)
            
            # Handle Optional types (Union[SomeType, None])
            original_field_type = field_type
            if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
                # Check if this is Optional[T] (which is Union[T, None])
                args = field_type.__args__
                if len(args) == 2 and type(None) in args:
                    # This is Optional[T], get the non-None type
                    field_type = next(arg for arg in args if arg is not type(None))
            
            # Check if this is a List type
            if hasattr(field_type, '__origin__') and field_type.__origin__ is list:
                # This is a List[SomeModel] field
                inner_type = field_type.__args__[0]
                
                if isinstance(field_value, list):
                    if not field_value:  # Empty list
                        # For empty lists, skip if optional or set empty list if required
                        if hasattr(field_info, 'is_required'):
                            is_required = field_info.is_required()
                        else:
                            is_required = getattr(field_info, 'required', True)
                        
                        if not is_required:
                            continue  # Skip empty optional list
                        else:
                            processed_data[field_name] = []  # Set empty list for required field
                    else:
                        # Convert list of dictionaries to list of model instances
                        if hasattr(inner_type, 'model_fields') or hasattr(inner_type, '__fields__'):
                            # inner_type is a Pydantic model
                            processed_instances = []
                            for item_data in field_value:
                                if isinstance(item_data, dict):
                                    # Recursively process nested model
                                    nested_instance = self.create_model_instance_from_form_data(item_data, inner_type)
                                    processed_instances.append(nested_instance)
                                else:
                                    # Simple value
                                    processed_instances.append(item_data)
                            processed_data[field_name] = processed_instances
                        else:
                            # List of simple types
                            processed_data[field_name] = field_value
                else:
                    processed_data[field_name] = field_value
            elif hasattr(field_type, 'model_fields') or hasattr(field_type, '__fields__'):
                # This is a nested model field
                if isinstance(field_value, dict):
                    processed_data[field_name] = self.create_model_instance_from_form_data(field_value, field_type)
                else:
                    processed_data[field_name] = field_value
            else:
                # Simple field
                processed_data[field_name] = field_value
        
        return model_class(**processed_data)
    
    def _find_schema_field_by_name(self, schema_field: SchemaField, field_name: str) -> Optional[SchemaField]:
        """Find a child schema field by name"""
        if not schema_field.children:
            return None
        
        for child in schema_field.children:
            if child.name == field_name:
                return child
        return None
    
    def generate_xml_from_form_data(self, form_data: Dict[str, Any], pretty_print: bool = True) -> str:
        """Generate XML directly from form data, bypassing Pydantic model conversion"""
        # Get the root element name
        root_name = self.xsd_parser.root_element.name if self.xsd_parser.root_element else "Root"
        
        # Create root element
        root = ET.Element(root_name)
        
        # Build XML tree directly from form data using XSD order
        root_schema = self.xsd_parser.parsed_structure
        self._build_xml_from_data(root, form_data, root_schema)
        
        # Convert to string
        if pretty_print:
            self._indent_xml(root)
        
        return ET.tostring(root, encoding='unicode')
    
    def generate_xml(self, model_instance: BaseModel, pretty_print: bool = True) -> str:
        """Generate XML string from a Pydantic model instance"""
        # Get the root element name
        root_name = self.xsd_parser.root_element.name if self.xsd_parser.root_element else "Root"
        
        # Create root element
        root = ET.Element(root_name)
        
        # Build XML tree from model
        self._build_xml_element(root, model_instance)
        
        # Convert to string
        if pretty_print:
            self._indent_xml(root)
        
        return ET.tostring(root, encoding='unicode')
    
    def _build_xml_from_data(self, parent: ET.Element, data: Dict[str, Any], schema_field: Optional['SchemaField'] = None):
        """Build XML elements directly from form data dictionary following XSD sequence order"""
        if schema_field and schema_field.children:
            # Use XSD order when schema information is available
            for child_schema in schema_field.children:
                field_name = child_schema.name
                
                # Get field value from data
                field_value = data.get(field_name)
                
                # Skip None values
                if field_value is None:
                    continue
                
                # Skip empty string values for optional fields
                if isinstance(field_value, str) and field_value.strip() == "":
                    continue
                
                # Process the field value in XSD order
                self._build_xml_field(parent, field_name, field_value, child_schema)
        else:
            # Fallback to dictionary order when no schema available
            for field_name, field_value in data.items():
                # Skip None values
                if field_value is None:
                    continue
                
                # Skip empty string values for optional fields
                if isinstance(field_value, str) and field_value.strip() == "":
                    continue
                
                # Process without schema information
                self._build_xml_field(parent, field_name, field_value, None)
    
    def _build_xml_field(self, parent: ET.Element, field_name: str, field_value: Any, schema_field: Optional[SchemaField] = None):
        """Build XML for a single field"""
        # Handle different value types
        if isinstance(field_value, list):
            # Handle lists - create multiple elements with same tag name
            if field_value:  # Only process non-empty lists
                for item in field_value:
                    item_element = ET.SubElement(parent, field_name)
                    if isinstance(item, dict):
                        # Dictionary item - build nested elements using schema field for this element
                        self._build_xml_from_data(item_element, item, schema_field)
                    else:
                        # Simple value
                        item_element.text = str(item)
        elif isinstance(field_value, dict):
            # Handle nested dictionaries
            child_element = ET.SubElement(parent, field_name)
            # Use the schema field for this nested element
            self._build_xml_from_data(child_element, field_value, schema_field)
        else:
            # Simple value
            child_element = ET.SubElement(parent, field_name)
            child_element.text = self._format_value(field_value)
    
    def _build_xml_element(self, parent: ET.Element, model_instance: BaseModel):
        """Recursively build XML elements from model instance"""
        for field_name, field_value in model_instance.dict().items():
            if field_value is None:
                continue
            
            # Skip empty string values for optional fields
            if isinstance(field_value, str) and field_value.strip() == "":
                continue
            
            # Handle different value types
            if isinstance(field_value, BaseModel):
                # Nested model - create element and recurse
                child_element = ET.SubElement(parent, field_name)
                self._build_xml_element(child_element, field_value)
            elif isinstance(field_value, list):
                # Handle lists - don't create wrapper element
                if field_value:  # Only process non-empty lists
                    for item in field_value:
                        item_element = ET.SubElement(parent, field_name)
                        if isinstance(item, BaseModel):
                            self._build_xml_element(item_element, item)
                        else:
                            item_element.text = str(item)
            elif isinstance(field_value, dict):
                # Handle dictionaries (shouldn't happen with proper conversion, but fallback)
                child_element = ET.SubElement(parent, field_name)
                for key, value in field_value.items():
                    if isinstance(value, (dict, list)):
                        # Nested complex structure - handle recursively
                        if isinstance(value, list):
                            # List of items
                            for item in value:
                                item_element = ET.SubElement(child_element, key)
                                if isinstance(item, dict):
                                    # Dictionary item - convert to XML elements
                                    for sub_key, sub_value in item.items():
                                        sub_element = ET.SubElement(item_element, sub_key)
                                        sub_element.text = str(sub_value)
                                else:
                                    item_element.text = str(item)
                        else:
                            # Single dictionary
                            dict_element = ET.SubElement(child_element, key)
                            for sub_key, sub_value in value.items():
                                sub_element = ET.SubElement(dict_element, sub_key)
                                sub_element.text = str(sub_value)
                    else:
                        dict_element = ET.SubElement(child_element, key)
                        dict_element.text = str(value)
            else:
                # Simple value
                child_element = ET.SubElement(parent, field_name)
                child_element.text = self._format_value(field_value)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for XML output"""
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (date, datetime)):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return str(value)
        else:
            return str(value)
    
    def _indent_xml(self, element: ET.Element, level: int = 0):
        """Add indentation to XML for pretty printing"""
        indent = "\n" + "  " * level
        if len(element):
            if not element.text or not element.text.strip():
                element.text = indent + "  "
            if not element.tail or not element.tail.strip():
                element.tail = indent
            for child in element:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not element.tail or not element.tail.strip()):
                element.tail = indent
    
    def validate_xml(self, xml_string: str) -> tuple[bool, List[str]]:
        """Validate XML string against the XSD schema"""
        try:
            # Parse XML
            xml_doc = etree.fromstring(xml_string.encode('utf-8'))
            
            # Validate against schema
            self.schema.validate(xml_doc)
            return True, []
            
        except xmlschema.XMLSchemaValidationError as e:
            return False, [str(e)]
        except etree.XMLSyntaxError as e:
            return False, [f"XML Syntax Error: {str(e)}"]
        except Exception as e:
            return False, [f"Validation Error: {str(e)}"]
    
    def generate_and_validate(self, model_instance: BaseModel, pretty_print: bool = True) -> tuple[str, bool, List[str]]:
        """Generate XML and validate it in one step"""
        xml_string = self.generate_xml(model_instance, pretty_print)
        is_valid, errors = self.validate_xml(xml_string)
        return xml_string, is_valid, errors
    
    def save_xml_to_file(self, xml_string: str, file_path: str):
        """Save XML string to file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_string)
    
    def load_xml_from_file(self, file_path: str) -> str:
        """Load XML string from file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def xml_to_dict(self, xml_string: str) -> Dict[str, Any]:
        """Convert XML string to dictionary"""
        try:
            xml_doc = etree.fromstring(xml_string.encode('utf-8'))
            return self._xml_element_to_dict(xml_doc)
        except Exception as e:
            raise ValueError(f"Failed to parse XML: {str(e)}")
    
    def _xml_element_to_dict(self, element: etree._Element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Handle attributes
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Handle text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            else:
                result['text'] = element.text.strip()
        
        # Handle child elements
        for child in element:
            child_dict = self._xml_element_to_dict(child)
            
            if child.tag in result:
                # Multiple elements with same tag - convert to list
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        
        return result
    
    def get_xml_preview(self, model_instance: BaseModel, max_length: int = 1000) -> str:
        """Get a preview of the generated XML"""
        xml_string = self.generate_xml(model_instance)
        if len(xml_string) > max_length:
            return xml_string[:max_length] + "..."
        return xml_string
    
    def compare_xml_files(self, file1_path: str, file2_path: str) -> Dict[str, Any]:
        """Compare two XML files"""
        try:
            xml1 = self.load_xml_from_file(file1_path)
            xml2 = self.load_xml_from_file(file2_path)
            
            dict1 = self.xml_to_dict(xml1)
            dict2 = self.xml_to_dict(xml2)
            
            return {
                'identical': dict1 == dict2,
                'differences': self._find_dict_differences(dict1, dict2)
            }
        except Exception as e:
            return {
                'error': str(e),
                'identical': False,
                'differences': []
            }
    
    def _find_dict_differences(self, dict1: Dict, dict2: Dict, path: str = "") -> List[str]:
        """Find differences between two dictionaries"""
        differences = []
        
        # Check keys in dict1
        for key in dict1:
            current_path = f"{path}.{key}" if path else key
            if key not in dict2:
                differences.append(f"Key '{current_path}' missing in second XML")
            elif isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                differences.extend(self._find_dict_differences(dict1[key], dict2[key], current_path))
            elif dict1[key] != dict2[key]:
                differences.append(f"Value difference at '{current_path}': '{dict1[key]}' vs '{dict2[key]}'")
        
        # Check keys in dict2 that are not in dict1
        for key in dict2:
            if key not in dict1:
                current_path = f"{path}.{key}" if path else key
                differences.append(f"Key '{current_path}' missing in first XML")
        
        return differences
    
    def validate_xml_file(self, file_path: str) -> tuple[bool, List[str]]:
        """Validate an XML file against the schema"""
        try:
            xml_string = self.load_xml_from_file(file_path)
            return self.validate_xml(xml_string)
        except Exception as e:
            return False, [f"Error reading file: {str(e)}"]