"""
XML Ingestion Module
Parses XML files and populates form data structures.
"""

import xml.etree.ElementTree as ET
from lxml import etree
from typing import Dict, List, Any, Optional, Union
import streamlit as st
from pathlib import Path

from .xsd_parser import XSDParser, SchemaField


class XMLIngestor:
    """Handles XML ingestion and form data population"""
    
    def __init__(self, xsd_parser: XSDParser):
        self.xsd_parser = xsd_parser
        self.form_data = {}
    
    def parse_xml_file(self, xml_file_path: str) -> Dict[str, Any]:
        """Parse XML file and return structured data"""
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            return self._xml_element_to_dict(root)
        except Exception as e:
            raise ValueError(f"Failed to parse XML file: {str(e)}")
    
    def parse_xml_string(self, xml_string: str) -> Dict[str, Any]:
        """Parse XML string and return structured data"""
        try:
            root = ET.fromstring(xml_string)
            return self._xml_element_to_dict(root)
        except Exception as e:
            raise ValueError(f"Failed to parse XML string: {str(e)}")
    
    def _xml_element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary recursively"""
        result = {}
        
        # Handle text content
        if element.text and element.text.strip():
            text_content = element.text.strip()
            if len(element) == 0:
                # Leaf element with text only
                return text_content
            else:
                # Element with both text and children
                result['_text'] = text_content
        
        # Handle child elements
        for child in element:
            child_name = child.tag
            child_dict = self._xml_element_to_dict(child)
            
            if child_name in result:
                # Multiple elements with same name - convert to list
                if not isinstance(result[child_name], list):
                    result[child_name] = [result[child_name]]
                result[child_name].append(child_dict)
            else:
                result[child_name] = child_dict
        
        return result
    
    def xml_to_form_data(self, xml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert parsed XML data to form data structure"""
        return self._flatten_xml_data(xml_data)
    
    def _flatten_xml_data(self, data: Dict[str, Any], parent_key: str = "") -> Dict[str, Any]:
        """Flatten nested XML data structure for form population"""
        result = {}
        
        for key, value in data.items():
            # Skip internal text markers
            if key == '_text':
                continue
                
            # Create full key path
            full_key = f"{parent_key}.{key}" if parent_key else key
            
            if isinstance(value, dict):
                # Nested dictionary - recurse
                nested_result = self._flatten_xml_data(value, full_key)
                result.update(nested_result)
            elif isinstance(value, list):
                # List of items - handle multiple entries
                result[key] = []
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        # Complex item - add to list as dict
                        result[key].append(self._flatten_xml_data(item))
                    else:
                        # Simple item - add as is
                        result[key].append(item)
            else:
                # Simple value
                result[key] = value
        
        return result
    
    def populate_form_from_xml(self, xml_file_path: str) -> Dict[str, Any]:
        """Main method to populate form data from XML file"""
        try:
            # Parse XML file
            xml_data = self.parse_xml_file(xml_file_path)
            
            # Convert to form data structure
            form_data = self.xml_to_form_data(xml_data)
            
            # Validate against XSD structure
            validated_data = self._validate_against_schema(form_data)
            
            return validated_data
            
        except Exception as e:
            st.error(f"Error processing XML file: {str(e)}")
            return {}
    
    def populate_form_from_xml_string(self, xml_string: str) -> Dict[str, Any]:
        """Main method to populate form data from XML string"""
        try:
            # Parse XML string
            xml_data = self.parse_xml_string(xml_string)
            
            # Convert to form data structure
            form_data = self.xml_to_form_data(xml_data)
            
            # Validate against XSD structure
            validated_data = self._validate_against_schema(form_data)
            
            return validated_data
            
        except Exception as e:
            st.error(f"Error processing XML string: {str(e)}")
            return {}
    
    def _validate_against_schema(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate form data against XSD schema and clean up invalid fields"""
        if not self.xsd_parser:
            return form_data
        
        validated_data = {}
        
        # Get all valid field names from XSD
        valid_fields = self._get_valid_field_names()
        
        for field_name, field_value in form_data.items():
            if field_name in valid_fields:
                # Field exists in schema - keep it
                validated_data[field_name] = field_value
            else:
                # Field not in schema - log warning but keep for now
                st.warning(f"Field '{field_name}' not found in XSD schema")
                validated_data[field_name] = field_value
        
        return validated_data
    
    def _get_valid_field_names(self) -> List[str]:
        """Get all valid field names from XSD schema"""
        valid_fields = []
        
        if self.xsd_parser and hasattr(self.xsd_parser, 'get_all_fields'):
            all_fields = self.xsd_parser.get_all_fields()
            valid_fields = [field.name for field in all_fields if hasattr(field, 'name')]
        
        return valid_fields
    
    def preview_xml_structure(self, xml_data: Dict[str, Any], max_depth: int = 3) -> str:
        """Generate a preview of the XML structure"""
        return self._format_structure(xml_data, depth=0, max_depth=max_depth)
    
    def _format_structure(self, data: Any, depth: int = 0, max_depth: int = 3) -> str:
        """Recursively format data structure for preview"""
        if depth > max_depth:
            return "... (truncated)"
        
        indent = "  " * depth
        
        if isinstance(data, dict):
            if not data:
                return "{}"
            
            items = []
            for key, value in data.items():
                if key == '_text':
                    continue
                
                if isinstance(value, (dict, list)):
                    formatted_value = self._format_structure(value, depth + 1, max_depth)
                    items.append(f"{indent}{key}: {formatted_value}")
                else:
                    # Truncate long values
                    str_value = str(value)
                    if len(str_value) > 50:
                        str_value = str_value[:50] + "..."
                    items.append(f"{indent}{key}: {repr(str_value)}")
            
            return "{\n" + ",\n".join(items) + f"\n{indent[:-2]}" + "}"
        
        elif isinstance(data, list):
            if not data:
                return "[]"
            
            items = []
            for i, item in enumerate(data[:3]):  # Show first 3 items
                formatted_item = self._format_structure(item, depth + 1, max_depth)
                items.append(f"{indent}{formatted_item}")
            
            if len(data) > 3:
                items.append(f"{indent}... ({len(data) - 3} more items)")
            
            return "[\n" + ",\n".join(items) + f"\n{indent[:-2]}" + "]"
        
        else:
            str_value = str(data)
            if len(str_value) > 100:
                str_value = str_value[:100] + "..."
            return repr(str_value)
    
    def get_xml_statistics(self, xml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about the XML data"""
        stats = {
            'total_fields': 0,
            'simple_fields': 0,
            'complex_fields': 0,
            'list_fields': 0,
            'field_names': []
        }
        
        self._collect_stats(xml_data, stats)
        
        return stats
    
    def _collect_stats(self, data: Any, stats: Dict[str, Any], parent_key: str = ""):
        """Recursively collect statistics about the data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == '_text':
                    continue
                    
                full_key = f"{parent_key}.{key}" if parent_key else key
                stats['field_names'].append(full_key)
                stats['total_fields'] += 1
                
                if isinstance(value, dict):
                    stats['complex_fields'] += 1
                    self._collect_stats(value, stats, full_key)
                elif isinstance(value, list):
                    stats['list_fields'] += 1
                    for item in value:
                        self._collect_stats(item, stats, full_key)
                else:
                    stats['simple_fields'] += 1
        
        elif isinstance(data, list):
            for item in data:
                self._collect_stats(item, stats, parent_key)
    
    def compare_xml_with_schema(self, xml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare XML data with XSD schema structure"""
        comparison = {
            'matching_fields': [],
            'missing_fields': [],
            'extra_fields': [],
            'type_mismatches': []
        }
        
        if not self.xsd_parser:
            return comparison
        
        # Get schema fields
        schema_fields = self._get_valid_field_names()
        xml_fields = []
        
        # Extract all field names from XML
        self._extract_field_names(xml_data, xml_fields)
        
        # Compare fields
        comparison['matching_fields'] = list(set(xml_fields) & set(schema_fields))
        comparison['missing_fields'] = list(set(schema_fields) - set(xml_fields))
        comparison['extra_fields'] = list(set(xml_fields) - set(schema_fields))
        
        return comparison
    
    def _extract_field_names(self, data: Any, field_names: List[str], parent_key: str = ""):
        """Extract all field names from XML data"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == '_text':
                    continue
                    
                full_key = f"{parent_key}.{key}" if parent_key else key
                field_names.append(key)  # Add simple key name
                
                if isinstance(value, (dict, list)):
                    self._extract_field_names(value, field_names, full_key)
        
        elif isinstance(data, list):
            for item in data:
                self._extract_field_names(item, field_names, parent_key)