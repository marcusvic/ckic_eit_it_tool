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

from .xsd_parser import XSDParser


class XMLEngine:
    """Generates and validates XML files from Pydantic models"""
    
    def __init__(self, xsd_parser: XSDParser):
        self.xsd_parser = xsd_parser
        self.schema = xmlschema.XMLSchema(xsd_parser.xsd_path)
    
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
    
    def _build_xml_element(self, parent: ET.Element, model_instance: BaseModel):
        """Recursively build XML elements from model instance"""
        for field_name, field_value in model_instance.dict().items():
            if field_value is None:
                continue
            
            # Create child element
            child_element = ET.SubElement(parent, field_name)
            
            # Handle different value types
            if isinstance(field_value, BaseModel):
                # Nested model - recurse
                self._build_xml_element(child_element, field_value)
            elif isinstance(field_value, list):
                # Handle lists
                parent.remove(child_element)  # Remove the wrapper element
                for item in field_value:
                    item_element = ET.SubElement(parent, field_name)
                    if isinstance(item, BaseModel):
                        self._build_xml_element(item_element, item)
                    else:
                        item_element.text = str(item)
            elif isinstance(field_value, dict):
                # Handle dictionaries
                for key, value in field_value.items():
                    dict_element = ET.SubElement(child_element, key)
                    dict_element.text = str(value)
            else:
                # Simple value
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