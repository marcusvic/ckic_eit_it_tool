# EIT Tool - Dynamic XML Generator

A Python application that dynamically generates XML files based on XSD schemas, with a user-friendly Streamlit interface for data collection and validation.
EIT instruction is [here](https://eitcloud365.sharepoint.com/sites/eitittool/Shared%20Documents/Forms/AllItems.aspx?viewid=9dc948f3%2D0134%2D4c69%2Dbf73%2Dfaf3e86fcc41&csf=1&web=1&e=5l5eNb&CID=f9ecb2a1%2D50bb%2D0000%2D00d3%2D0144107de335&cidOR=SPO&FolderCTID=0x012000066028B80C57DF47890C12462FC2847D)

## Features

- **Dynamic Schema Processing**: Automatically adapts to any XSD schema
- **User-Friendly Interface**: Streamlit-based form with real-time validation
- **XML Generation**: Creates valid XML files from collected data
- **Schema Validation**: Validates XML against XSD schemas
- **API Integration**: REST API for system-to-system integration
- **Extensible Architecture**: Easy to extend with new features

## Architecture

The application follows a modular architecture:

- **XSD Parser**: Analyzes XSD schemas dynamically
- **Data Model Generator**: Creates Pydantic models from XSD structure
- **Form Generator**: Generates Streamlit UI components
- **XML Engine**: Handles XML generation and validation
- **API Interface**: REST endpoints for integration

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ckic_eit_it_tool
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Ensure you have an XSD file in the project directory

## Usage

### Running the Streamlit Application

```bash
streamlit run app.py
```

This will start the web interface at `http://localhost:8501`

### Using the Web Interface

1. **Load Schema**: Upload or select an XSD file
2. **Enter Data**: Fill out the dynamically generated form
3. **Preview XML**: See the generated XML in real-time
4. **Validate**: Check if your XML conforms to the schema
5. **Export**: Download the generated XML file

### Running the API Server

```bash
python api/api_interface.py
```

Or using uvicorn:
```bash
uvicorn api.api_interface:app --host 0.0.0.0 --port 8000
```

API documentation will be available at `http://localhost:8000/docs`

### API Endpoints

- `POST /schema/load` - Load XSD schema
- `GET /schema/info` - Get schema information
- `GET /schema/fields` - Get schema fields
- `POST /xml/generate` - Generate XML from data
- `POST /xml/validate` - Validate XML content
- `POST /xml/export` - Export XML file

## Configuration

Environment variables for configuration:

- `EIT_API_HOST`: API host (default: 0.0.0.0)
- `EIT_API_PORT`: API port (default: 8000)
- `EIT_SCHEMAS_DIR`: Directory for XSD files (default: data/schemas)
- `EIT_OUTPUT_DIR`: Directory for output files (default: output)
- `EIT_STRICT_VALIDATION`: Enable strict validation (default: true)

## Project Structure

```
eit_tool/
├── app.py                           # Main Streamlit application
├── requirements.txt                 # Python dependencies
├── README.md                        # Project documentation
├── EIT IT Tool - Extended_projects_v1.16.xsd  # Sample XSD schema
├── PROJ_EIT-CLIMATE_KIC_230040 1.xml          # Sample XML output
├── core/                            # Core application modules
│   ├── __init__.py
│   ├── xsd_parser.py               # XSD parsing and analysis
│   ├── data_model.py               # Dynamic Pydantic model generation
│   ├── form_generator.py           # Basic form generation
│   ├── complex_form_generator.py   # Advanced hierarchical forms
│   └── xml_engine.py               # XML generation and validation
├── api/                            # REST API interface
│   ├── __init__.py
│   └── api_interface.py            # FastAPI endpoints
├── config/                         # Configuration management
│   ├── __init__.py
│   └── config.py                   # Application settings
└── tests/                          # Test suite
    ├── __init__.py
    └── test_basic.py               # Basic functionality tests
```

## Testing

Run the tests:
```bash
pytest tests/
```

## Dependencies

- **Python 3.9+**: Core language
- **Streamlit**: Web interface framework
- **lxml**: XML processing
- **xmlschema**: XSD parsing and validation
- **Pydantic**: Data validation and modeling
- **FastAPI**: API framework
- **pytest**: Testing framework

## Example Usage

1. **Load an XSD schema** (e.g., EIT IT Tool - Extended_projects_v1.16.xsd)
2. **Fill the form** with project information
3. **Generate XML** that conforms to the schema
4. **Validate and export** the XML file

## Future Enhancements

- Database integration for data persistence
- Advanced form validation
- Bulk XML generation
- Integration with external systems
- User authentication and authorization
- Custom field types and widgets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository or contact the development team.