"""
API Interface Module
REST API endpoints for future system integrations.
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import tempfile
import os
from datetime import datetime

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.xml_engine import XMLEngine


# Initialize FastAPI app
app = FastAPI(
    title="EIT Tool API",
    description="Dynamic XML generation API based on XSD schemas",
    version="1.0.0"
)

# Global variables to store current schema context
current_xsd_parser: Optional[XSDParser] = None
current_data_model_generator: Optional[DataModelGenerator] = None
current_xml_engine: Optional[XMLEngine] = None
current_root_model = None


class SchemaInfo(BaseModel):
    """Schema information response model"""
    root_element: str
    namespace: Optional[str]
    fields_count: int
    loaded_at: datetime


class ValidationResult(BaseModel):
    """Validation result response model"""
    is_valid: bool
    errors: List[str]


class XMLGenerationRequest(BaseModel):
    """XML generation request model"""
    data: Dict[str, Any]
    pretty_print: bool = True


class XMLGenerationResponse(BaseModel):
    """XML generation response model"""
    xml_content: str
    is_valid: bool
    validation_errors: List[str]
    size_bytes: int


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "EIT Tool API - Dynamic XML Generator"}


@app.post("/schema/load")
async def load_schema(xsd_file: UploadFile = File(...)):
    """Load XSD schema from uploaded file"""
    global current_xsd_parser, current_data_model_generator, current_xml_engine, current_root_model
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xsd') as tmp_file:
            content = await xsd_file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Initialize parser
        xsd_parser = XSDParser(tmp_path)
        parsed_data = xsd_parser.parse()
        
        # Initialize data model generator
        data_model_generator = DataModelGenerator(xsd_parser)
        models = data_model_generator.generate_models()
        
        # Get root model
        root_model = models[parsed_data['root_element']]
        
        # Initialize XML engine
        xml_engine = XMLEngine(xsd_parser)
        
        # Store globally
        current_xsd_parser = xsd_parser
        current_data_model_generator = data_model_generator
        current_xml_engine = xml_engine
        current_root_model = root_model
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        return SchemaInfo(
            root_element=parsed_data['root_element'],
            namespace=parsed_data.get('namespace'),
            fields_count=len(xsd_parser.get_all_fields()),
            loaded_at=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load schema: {str(e)}")


@app.get("/schema/info")
async def get_schema_info():
    """Get current schema information"""
    if current_xsd_parser is None:
        raise HTTPException(status_code=404, detail="No schema loaded")
    
    return SchemaInfo(
        root_element=current_xsd_parser.root_element.name,
        namespace=current_xsd_parser.schema.target_namespace,
        fields_count=len(current_xsd_parser.get_all_fields()),
        loaded_at=datetime.now()
    )


@app.get("/schema/fields")
async def get_schema_fields():
    """Get schema fields information"""
    if current_data_model_generator is None or current_root_model is None:
        raise HTTPException(status_code=404, detail="No schema loaded")
    
    try:
        fields_info = current_data_model_generator.get_model_fields_info(current_root_model)
        return fields_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get fields info: {str(e)}")


@app.post("/xml/generate")
async def generate_xml(request: XMLGenerationRequest):
    """Generate XML from provided data"""
    if current_root_model is None or current_xml_engine is None:
        raise HTTPException(status_code=404, detail="No schema loaded")
    
    try:
        # Create model instance
        model_instance = current_root_model(**request.data)
        
        # Generate XML
        xml_content, is_valid, validation_errors = current_xml_engine.generate_and_validate(
            model_instance, request.pretty_print
        )
        
        return XMLGenerationResponse(
            xml_content=xml_content,
            is_valid=is_valid,
            validation_errors=validation_errors,
            size_bytes=len(xml_content.encode('utf-8'))
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate XML: {str(e)}")


@app.post("/xml/validate")
async def validate_xml(xml_content: str = Form(...)):
    """Validate XML content against current schema"""
    if current_xml_engine is None:
        raise HTTPException(status_code=404, detail="No schema loaded")
    
    try:
        is_valid, errors = current_xml_engine.validate_xml(xml_content)
        return ValidationResult(is_valid=is_valid, errors=errors)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate XML: {str(e)}")


@app.post("/xml/validate-file")
async def validate_xml_file(xml_file: UploadFile = File(...)):
    """Validate XML file against current schema"""
    if current_xml_engine is None:
        raise HTTPException(status_code=404, detail="No schema loaded")
    
    try:
        content = await xml_file.read()
        xml_content = content.decode('utf-8')
        
        is_valid, errors = current_xml_engine.validate_xml(xml_content)
        return ValidationResult(is_valid=is_valid, errors=errors)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate XML file: {str(e)}")


@app.post("/xml/convert")
async def convert_xml_to_data(xml_content: str = Form(...)):
    """Convert XML content to data dictionary"""
    if current_xml_engine is None:
        raise HTTPException(status_code=404, detail="No schema loaded")
    
    try:
        data_dict = current_xml_engine.xml_to_dict(xml_content)
        return {"data": data_dict}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to convert XML: {str(e)}")


@app.post("/xml/export")
async def export_xml(request: XMLGenerationRequest):
    """Generate and export XML file"""
    if current_root_model is None or current_xml_engine is None:
        raise HTTPException(status_code=404, detail="No schema loaded")
    
    try:
        # Create model instance
        model_instance = current_root_model(**request.data)
        
        # Generate XML
        xml_content = current_xml_engine.generate_xml(model_instance, request.pretty_print)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as tmp_file:
            tmp_file.write(xml_content)
            tmp_path = tmp_file.name
        
        return FileResponse(
            tmp_path,
            filename=f"generated_xml_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml",
            media_type="application/xml"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to export XML: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "schema_loaded": current_xsd_parser is not None
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request, exc):
    return HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)