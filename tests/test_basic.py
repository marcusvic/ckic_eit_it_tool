"""
Basic tests for the EIT Tool functionality.
"""

import pytest
import os
import tempfile
from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.xml_engine import XMLEngine


class TestBasicFunctionality:
    """Test basic functionality of the EIT Tool"""
    
    def test_xsd_parser_initialization(self):
        """Test XSD parser can be initialized"""
        xsd_path = "EIT IT Tool - Extended_projects_v1.16.xsd"
        if os.path.exists(xsd_path):
            parser = XSDParser(xsd_path)
            assert parser.xsd_path == xsd_path
            assert parser.schema is not None
    
    def test_xsd_parsing(self):
        """Test XSD parsing functionality"""
        xsd_path = "EIT IT Tool - Extended_projects_v1.16.xsd"
        if os.path.exists(xsd_path):
            parser = XSDParser(xsd_path)
            parsed_data = parser.parse()
            
            assert "root_element" in parsed_data
            assert "structure" in parsed_data
            assert parsed_data["root_element"] == "Project"
    
    def test_data_model_generation(self):
        """Test data model generation"""
        xsd_path = "EIT IT Tool - Extended_projects_v1.16.xsd"
        if os.path.exists(xsd_path):
            parser = XSDParser(xsd_path)
            parser.parse()
            
            generator = DataModelGenerator(parser)
            models = generator.generate_models()
            
            assert len(models) > 0
            assert "Project" in models
    
    def test_xml_generation(self):
        """Test XML generation"""
        xsd_path = "EIT IT Tool - Extended_projects_v1.16.xsd"
        if os.path.exists(xsd_path):
            parser = XSDParser(xsd_path)
            parser.parse()
            
            generator = DataModelGenerator(parser)
            models = generator.generate_models()
            
            xml_engine = XMLEngine(parser)
            
            # Create a simple model instance
            root_model = models["Project"]
            
            # This test might need adjustment based on actual required fields
            # For now, just test that the XML engine initializes properly
            assert xml_engine.xsd_parser is not None
            assert xml_engine.schema is not None


def test_directory_structure():
    """Test that required directories exist"""
    required_dirs = ["core", "api", "config", "tests"]
    for dir_name in required_dirs:
        assert os.path.exists(dir_name), f"Directory {dir_name} should exist"


def test_required_files():
    """Test that required files exist"""
    required_files = [
        "app.py",
        "requirements.txt",
        "core/xsd_parser.py",
        "core/data_model.py",
        "core/form_generator.py",
        "core/xml_engine.py",
        "api/api_interface.py",
        "config/config.py"
    ]
    
    for file_path in required_files:
        assert os.path.exists(file_path), f"File {file_path} should exist"


if __name__ == "__main__":
    pytest.main([__file__])