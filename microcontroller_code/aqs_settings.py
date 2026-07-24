def load_settings(path="aqs_settings.toml"):
    """Parse a simple TOML file into a flat dict with 'section.key' keys.
    Supports strings, booleans, ints, and floats. Lines starting with # are comments."""
    settings = {}
    section = ""
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Section header
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1].strip()
                    continue
                # Key = value
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Strip inline comments
                for i, ch in enumerate(value):
                    if ch == "#" and (i == 0 or value[i - 1] == " "):
                        value = value[:i].strip()
                        break
                # Parse value type
                value = _parse_value(value)
                full_key = f"{section}.{key}" if section else key
                settings[full_key] = value
    except OSError:
        print(f"Settings file '{path}' not found, using defaults.")
    return settings


def _parse_value(value):
    """Convert a TOML value string to a Python type."""
    # String
    if (value.startswith('"') and value.endswith('"')) or \
       (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    # Boolean
    lower = value.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    # Number
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
