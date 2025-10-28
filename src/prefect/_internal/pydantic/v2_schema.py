import inspect
import typing
import typing as t

import pydantic
from pydantic import BaseModel as V2BaseModel
from pydantic import ConfigDict, PydanticUndefinedAnnotation, create_model
from pydantic.type_adapter import TypeAdapter

from prefect._internal.pydantic.schemas import GenerateEmptySchemaForUserClasses


def is_v2_model(v: t.Any) -> bool:
    if isinstance(v, V2BaseModel):
        return True
    try:
        if inspect.isclass(v) and issubclass(v, V2BaseModel):
            return True
    except TypeError:
        pass

    return False


def is_v2_type(v: t.Any) -> bool:
    if is_v2_model(v):
        return True

    try:
        return v.__module__.startswith("pydantic.types")
    except AttributeError:
        return False


def has_v2_type_as_param(signature: inspect.Signature) -> bool:
    parameters = signature.parameters.values()
    for p in parameters:
        # check if this parameter is a v2 model
        if is_v2_type(p.annotation):
            return True

        # check if this parameter is a collection of types
        for v in typing.get_args(p.annotation):
            if is_v2_type(v):
                return True
    return False


def _flatten_uploaded_file_refs(schema: dict[str, t.Any]) -> None:
    """
    Post-process a JSON schema to flatten UploadedFile references.

    Replaces references to UploadedFile with a simple string type with format: base64.
    This allows the UI to render a file upload field instead of a complex object form.

    The function modifies the schema in-place.
    """
    # Check if this schema has properties (parameter definitions)
    if "properties" not in schema:
        return

    properties = schema["properties"]
    # Check both definitions and $defs (pydantic v2 uses $defs)
    definitions = schema.get("definitions", {})
    if not definitions and "$defs" in schema:
        definitions = schema["$defs"]

    # Look for UploadedFile references in properties
    for prop_name, prop_schema in list(properties.items()):
        replaced = False

        # Check if this property references UploadedFile
        if "$ref" in prop_schema:
            ref = prop_schema["$ref"]
            # Extract the definition name from the reference
            # e.g., "#/definitions/UploadedFile" -> "UploadedFile"
            # or "#/$defs/UploadedFile" -> "UploadedFile"
            if "/" in ref:
                def_name = ref.split("/")[-1]
                # Check if this is an UploadedFile by looking at the definition
                if def_name in definitions:
                    definition = definitions[def_name]
                    # Check if this definition has the structure of UploadedFile
                    # (has a 'content' field with format: base64)
                    if _is_uploaded_file_definition(definition):
                        # Replace the reference with a simple string + format: base64
                        properties[prop_name] = {
                            "type": "string",
                            "format": "base64",
                            "title": prop_schema.get("title", prop_name),
                            "description": definition.get("description", "Upload a file"),
                        }
                        replaced = True

        # Also check for allOf pattern which pydantic sometimes uses
        if not replaced and "allOf" in prop_schema:
            for item in prop_schema["allOf"]:
                if "$ref" in item:
                    ref = item["$ref"]
                    if "/" in ref:
                        def_name = ref.split("/")[-1]
                        if def_name in definitions:
                            definition = definitions[def_name]
                            if _is_uploaded_file_definition(definition):
                                # Get title from allOf structure if present
                                title = prop_schema.get("title", prop_name)
                                desc = definition.get("description", "Upload a file")
                                properties[prop_name] = {
                                    "type": "string",
                                    "format": "base64",
                                    "title": title,
                                    "description": desc,
                                }
                                break


def _is_uploaded_file_definition(definition: dict[str, t.Any]) -> bool:
    """
    Check if a schema definition represents an UploadedFile type.

    Returns True if the definition has a 'content' property with format: base64.
    """
    if "properties" not in definition:
        return False

    properties = definition["properties"]

    # Check for 'content' field with format: base64
    content_prop = properties.get("content", {})

    # Check if format is directly on the property
    if content_prop.get("format") == "base64":
        return True

    # Check in json_schema_extra (sometimes pydantic puts it there)
    if "json_schema_extra" in content_prop:
        extra = content_prop["json_schema_extra"]
        if isinstance(extra, dict) and extra.get("format") == "base64":
            return True

    # Check if content has allOf with format
    if "allOf" in content_prop:
        for item in content_prop["allOf"]:
            if item.get("format") == "base64":
                return True

    # Also check the definition title to see if it contains "UploadedFile"
    if "UploadedFile" in definition.get("title", ""):
        return True

    return False


def process_v2_params(
    param: inspect.Parameter,
    *,
    position: int,
    docstrings: dict[str, str],
    aliases: dict[str, str],
) -> tuple[str, t.Any, t.Any]:
    """
    Generate a sanitized name, type, and pydantic.Field for a given parameter.

    This implementation is exactly the same as the v1 implementation except
    that it uses pydantic v2 constructs.
    """
    # Pydantic model creation will fail if names collide with the BaseModel type
    if hasattr(pydantic.BaseModel, param.name):
        name = param.name + "__"
        aliases[name] = param.name
    else:
        name = param.name

    type_ = t.Any if param.annotation is inspect.Parameter.empty else param.annotation

    field = pydantic.Field(
        default=... if param.default is param.empty else param.default,
        title=param.name,
        description=docstrings.get(param.name, None),
        alias=aliases.get(name),
        json_schema_extra={"position": position},
    )
    return name, type_, field


def create_v2_schema(
    name_: str,
    model_cfg: t.Optional[ConfigDict] = None,
    model_base: t.Optional[type[V2BaseModel]] = None,
    model_fields: t.Optional[dict[str, t.Any]] = None,
) -> dict[str, t.Any]:
    """
    Create a pydantic v2 model and craft a v1 compatible schema from it.
    """
    model_fields = model_fields or {}
    model = create_model(
        name_, __config__=model_cfg, __base__=model_base, **model_fields
    )
    try:
        adapter = TypeAdapter(model)
    except PydanticUndefinedAnnotation as exc:
        # in v1 this raises a TypeError, which is handled by parameter_schema
        raise TypeError(exc.message)

    # root model references under #definitions
    schema = adapter.json_schema(
        by_alias=True,
        ref_template="#/definitions/{model}",
        schema_generator=GenerateEmptySchemaForUserClasses,
    )
    # ensure backwards compatibility by copying $defs into definitions
    if "$defs" in schema:
        schema["definitions"] = schema["$defs"]

    # Post-process: flatten UploadedFile references to string with format: base64
    # This allows the UI to render a simple file upload field instead of an object
    _flatten_uploaded_file_refs(schema)

    return schema
