"""
Core package for EIT Tool.
Contains the main functionality for XSD parsing, data modeling, and XML generation.
"""

from .xsd_parser import XSDParser
from .data_model import DataModelGenerator
from .form_generator import FormGenerator
from .xml_engine import XMLEngine

__all__ = [
    'XSDParser',
    'DataModelGenerator', 
    'FormGenerator',
    'XMLEngine'
]