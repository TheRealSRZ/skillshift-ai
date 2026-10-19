def validate_source_record(source: dict) -> bool:
    required = ('id', 'title', 'geography', 'source_type')
    return all(bool(source.get(key)) for key in required)
