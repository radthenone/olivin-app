# utils/allauth_schema_hook.py
import json
import logging
from urllib.error import URLError
from urllib.request import urlopen

from django.conf import settings

logger = logging.getLogger(__name__)

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "options", "head"})


def _get_spec_url() -> str:
    base = getattr(settings, "ALLAUTH_SPEC_BASE_URL", "http://localhost:8000")
    return f"{base}/_allauth/openapi.json"


def _fix_operation_id(path: str, method: str, operation: dict) -> None:
    if not operation.get("operationId"):
        clean_path = path.strip("/").replace("/", "_").replace("{", "").replace("}", "")
        operation["operationId"] = f"allauth_{method}_{clean_path}"


def _fix_tags(operation: dict) -> None:
    if not operation.get("tags"):
        operation["tags"] = ["allauth"]


def _fix_parameters(operation: dict) -> None:
    operation["parameters"] = [
        param
        for param in operation.get("parameters", [])
        if isinstance(param, dict) and ("$ref" in param or ("in" in param and "name" in param))
        #                               ↑ zachowaj $ref bez sprawdzania name/in
    ]


def _fix_operation(path: str, method: str, operation: dict) -> dict:
    if not isinstance(operation, dict):
        return operation
    _fix_operation_id(path, method, operation)
    _fix_tags(operation)
    _fix_parameters(operation)
    return operation


def _inject_path_params(operation: dict, path_level_params: list) -> None:
    if not path_level_params:
        return
    existing_params = operation.get("parameters", [])
    existing_names = {p.get("name") for p in existing_params if isinstance(p, dict)}
    for param in path_level_params:
        if isinstance(param, dict) and param.get("name") not in existing_names:
            existing_params.append(param)
    operation["parameters"] = existing_params


def _merge_components(result: dict, allauth: dict) -> None:
    for section, schemas in allauth.get("components", {}).items():
        if not isinstance(schemas, dict):
            continue
        existing = result.setdefault("components", {}).setdefault(section, {})
        for key, value in schemas.items():
            existing.setdefault(key, value)



def _merge_paths(result: dict, allauth: dict) -> None:
    for path, path_item in allauth.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue

        path_level_params = path_item.get("parameters", [])

        fixed_methods = {}
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            if not isinstance(operation, dict):
                continue

            _inject_path_params(operation, path_level_params)
            fixed_methods[method] = _fix_operation(path, method, operation)

        if fixed_methods:
            result["paths"].setdefault(path, {}).update(fixed_methods)


def _fetch_allauth_schema() -> dict | None:
    try:
        with urlopen(_get_spec_url(), timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, Exception) as e:
        logger.warning(f"inject_allauth_schema: błąd fetch: {e}")
        return None


def inject_allauth_schema(result, generator, request, public) -> dict:
    if not settings.DEBUG:
        return result

    allauth = _fetch_allauth_schema()
    if allauth is None:
        return result

    try:
        _merge_components(result, allauth)
        _merge_paths(result, allauth)
    except Exception as e:
        logger.warning(f"inject_allauth_schema failed: {e}", exc_info=True)

    return result
