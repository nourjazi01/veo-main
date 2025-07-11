"""
Utility functions for working with Pydantic models and JSON validation.
"""

import json
from typing import Dict, Any, Union, Type
from pathlib import Path
import logging
from pydantic import BaseModel, ValidationError

from schemas import (
    DocumentAnalysisOutput, 
    CandidateMatchingOutput, 
    ReportGenerationOutput
)

logger = logging.getLogger(__name__)


class ModelValidator:
    """Handles validation and conversion of JSON data to Pydantic models."""
    
    MODEL_MAPPING = {
        'document_analysis': DocumentAnalysisOutput,
        'candidate_matching': CandidateMatchingOutput,
        'report_generation': ReportGenerationOutput
    }
    
    @staticmethod
    def validate_json_string(json_str: str, model_type: str) -> Union[BaseModel, Dict[str, Any]]:
        """
        Validate a JSON string against a specific model type.
        
        Args:
            json_str: JSON string to validate
            model_type: Type of model to validate against ('document_analysis', 'candidate_matching', 'report_generation')
            
        Returns:
            Validated Pydantic model instance or original dict if validation fails
        """
        try:
            # Parse JSON string
            data = json.loads(json_str)
            return ModelValidator.validate_dict(data, model_type)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON string: {e}")
            return {"error": f"Invalid JSON: {e}"}
    
    @staticmethod
    def validate_dict(data: Dict[str, Any], model_type: str) -> Union[BaseModel, Dict[str, Any]]:
        """
        Validate a dictionary against a specific model type.
        
        Args:
            data: Dictionary to validate
            model_type: Type of model to validate against
            
        Returns:
            Validated Pydantic model instance or original dict if validation fails
        """
        if model_type not in ModelValidator.MODEL_MAPPING:
            logger.error(f"Unknown model type: {model_type}")
            return {"error": f"Unknown model type: {model_type}"}
        
        model_class = ModelValidator.MODEL_MAPPING[model_type]
        
        try:
            # Create and validate model instance
            model_instance = model_class(**data)
            logger.info(f"Successfully validated {model_type} model")
            return model_instance
        except ValidationError as e:
            logger.error(f"Validation error for {model_type}: {e}")
            return {"error": f"Validation error: {e}", "original_data": data}
    
    @staticmethod
    def validate_file(file_path: Union[str, Path], model_type: str) -> Union[BaseModel, Dict[str, Any]]:
        """
        Validate a JSON file against a specific model type.
        
        Args:
            file_path: Path to JSON file
            model_type: Type of model to validate against
            
        Returns:
            Validated Pydantic model instance or error dict
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ModelValidator.validate_dict(data, model_type)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return {"error": f"File not found: {file_path}"}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {file_path}: {e}")
            return {"error": f"Invalid JSON in file: {e}"}
    
    @staticmethod
    def model_to_dict(model: BaseModel) -> Dict[str, Any]:
        """Convert a Pydantic model to a dictionary."""
        return model.model_dump()
    
    @staticmethod
    def model_to_json(model: BaseModel, indent: int = 2) -> str:
        """Convert a Pydantic model to a JSON string."""
        return model.model_dump_json(indent=indent)
    
    @staticmethod
    def save_model_to_file(model: BaseModel, file_path: Union[str, Path]) -> bool:
        """
        Save a Pydantic model to a JSON file.
        
        Args:
            model: Pydantic model instance
            file_path: Path to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(ModelValidator.model_to_json(model))
            logger.info(f"Successfully saved model to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving model to file {file_path}: {e}")
            return False


class SchemaDocumentationGenerator:
    """Generates documentation for the schemas."""
    
    @staticmethod
    def generate_field_documentation(model_class: Type[BaseModel]) -> Dict[str, Any]:
        """Generate documentation for all fields in a model."""
        fields_doc = {}
        
        for field_name, field_info in model_class.model_fields.items():
            fields_doc[field_name] = {
                "type": str(field_info.annotation),
                "description": field_info.description or "No description provided",
                "required": field_info.is_required(),
                "default": field_info.default if field_info.default is not None else "No default"
            }
        
        return fields_doc
    
    @staticmethod
    def generate_schema_documentation() -> Dict[str, Any]:
        """Generate complete documentation for all schemas."""
        documentation = {}
        
        for model_name, model_class in ModelValidator.MODEL_MAPPING.items():
            documentation[model_name] = {
                "model_class": model_class.__name__,
                "description": model_class.__doc__ or "No description provided",
                "fields": SchemaDocumentationGenerator.generate_field_documentation(model_class)
            }
        
        return documentation
    
    @staticmethod
    def save_documentation_to_file(file_path: Union[str, Path]) -> bool:
        """Save schema documentation to a JSON file."""
        try:
            docs = SchemaDocumentationGenerator.generate_schema_documentation()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(docs, f, indent=2, default=str)
            logger.info(f"Documentation saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving documentation: {e}")
            return False
