"""Cosmic Standard Library — json_utils module."""
from __future__ import annotations
import json
from typing import Any, Callable


def load(path: str) -> Any:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def loads(s: str) -> Any:
    return json.loads(s)


def dumps(obj: Any, indent: int = 2) -> str:
    return json.dumps(obj, indent=indent, default=str, ensure_ascii=False)


def pretty(obj: Any) -> str:
    return dumps(obj, indent=2)


def validate(data: Any, schema: dict) -> tuple[bool, list[str]]:
    errors = []
    if 'type' in schema:
        type_map = {'string': str, 'number': (int, float), 'integer': int,
                    'boolean': bool, 'array': list, 'object': dict, 'null': type(None)}
        expected = type_map.get(schema['type'])
        if expected and not isinstance(data, expected):
            errors.append(f"Expected type {schema['type']}, got {type(data).__name__}")
    if 'required' in schema and isinstance(data, dict):
        for key in schema['required']:
            if key not in data:
                errors.append(f"Missing required field: {key}")
    if 'properties' in schema and isinstance(data, dict):
        for key, prop_schema in schema['properties'].items():
            if key in data:
                valid, errs = validate(data[key], prop_schema)
                if not valid:
                    errors.extend([f"{key}.{e}" for e in errs])
    return len(errors) == 0, errors


def patch(data: dict, patch_doc: dict) -> dict:
    result = dict(data)
    for key, value in patch_doc.items():
        if value is None:
            result.pop(key, None)
        elif isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = patch(result[key], value)
        else:
            result[key] = value
    return result


def merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def diff(a: Any, b: Any, path: str = '') -> list[dict[str, Any]]:
    changes = []
    if type(a) != type(b):
        changes.append({'op': 'replace', 'path': path, 'value': b})
    elif isinstance(a, dict) and isinstance(b, dict):
        all_keys = set(list(a.keys()) + list(b.keys()))
        for key in all_keys:
            child_path = f"{path}/{key}" if path else key
            if key not in a:
                changes.append({'op': 'add', 'path': child_path, 'value': b[key]})
            elif key not in b:
                changes.append({'op': 'remove', 'path': child_path})
            else:
                changes.extend(diff(a[key], b[key], child_path))
    elif isinstance(a, list) and isinstance(b, list):
        max_len = max(len(a), len(b))
        for i in range(max_len):
            child_path = f"{path}/{i}"
            if i >= len(a):
                changes.append({'op': 'add', 'path': child_path, 'value': b[i]})
            elif i >= len(b):
                changes.append({'op': 'remove', 'path': child_path})
            else:
                changes.extend(diff(a[i], b[i], child_path))
    elif a != b:
        changes.append({'op': 'replace', 'path': path, 'value': b})
    return changes


def flatten(data: dict, prefix: str = '') -> dict[str, Any]:
    result = {}
    for key, value in data.items():
        new_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten(value, new_key))
        else:
            result[new_key] = value
    return result


def unflatten(data: dict[str, Any]) -> dict:
    result = {}
    for key, value in data.items():
        parts = key.split('.')
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def query(data: Any, path: str) -> Any:
    parts = path.strip('/').split('/')
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


def transform(data: Any, func: Callable) -> Any:
    if isinstance(data, dict):
        return {k: transform(v, func) for k, v in data.items()}
    elif isinstance(data, list):
        return [transform(item, func) for item in data]
    else:
        return func(data)


def schema_validate(data: Any, schema: dict) -> list[str]:
    return validate(data, schema)[1]


def to_jsonl(data: list[dict]) -> str:
    return '\n'.join(json.dumps(item, default=str) for item in data)


def from_jsonl(text: str) -> list[dict]:
    return [json.loads(line) for line in text.strip().split('\n') if line.strip()]


def compact(obj: Any) -> str:
    return json.dumps(obj, separators=(',', ':'), default=str, ensure_ascii=False)
