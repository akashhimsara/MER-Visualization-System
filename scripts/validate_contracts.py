import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]

SCHEMA_DIR = ROOT / "contracts" / "schemas"
EXAMPLE_DIR = ROOT / "contracts" / "examples"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def validate_schemas():
    failed = False
    schema_files = sorted(SCHEMA_DIR.glob("*.schema.json"))

    if not schema_files:
        print("No contract schemas found.")
        return True

    print("Checking schemas...")

    for schema_path in schema_files:
        try:
            schema = load_json(schema_path)
            Draft202012Validator.check_schema(schema)
            print(f"[SCHEMA OK] {schema_path.name}")
        except Exception as error:
            failed = True
            print(f"[SCHEMA ERROR] {schema_path.name}")
            print(f"  {error}")

    return failed


def validate_examples():
    failed = False

    print("\nChecking examples...")

    example_files = sorted(EXAMPLE_DIR.glob("*.example.json"))

    if not example_files:
        print("No contract examples found.")
        return True

    for example_path in example_files:
        schema_name = example_path.name.replace(
            ".example.json",
            ".schema.json"
        )

        schema_path = SCHEMA_DIR / schema_name

        if not schema_path.exists():
            failed = True
            print(
                f"[MISSING SCHEMA] "
                f"{example_path.name} -> {schema_name}"
            )
            continue

        try:
            schema = load_json(schema_path)
            example = load_json(example_path)

            validator = Draft202012Validator(schema)

            errors = sorted(
                validator.iter_errors(example),
                key=lambda error: list(error.path)
            )

            if errors:
                failed = True
                print(f"[FAILED] {example_path.name}")

                for error in errors:
                    location = ".".join(
                        str(part) for part in error.path
                    )

                    if not location:
                        location = "<root>"

                    print(f"  {location}: {error.message}")
            else:
                print(f"[PASS] {example_path.name}")

        except Exception as error:
            failed = True
            print(f"[ERROR] {example_path.name}")
            print(f"  {error}")

    return failed


def check_pair_counts():
    failed = False

    schema_names = {
        path.name.replace(".schema.json", "")
        for path in SCHEMA_DIR.glob("*.schema.json")
    }

    example_names = {
        path.name.replace(".example.json", "")
        for path in EXAMPLE_DIR.glob("*.example.json")
    }

    missing_examples = schema_names - example_names
    missing_schemas = example_names - schema_names

    if missing_examples:
        failed = True
        for name in sorted(missing_examples):
            print(f"[MISSING EXAMPLE] {name}.example.json")

    if missing_schemas:
        failed = True
        for name in sorted(missing_schemas):
            print(f"[MISSING SCHEMA] {name}.schema.json")

    return failed


def main():
    failed = False

    if not SCHEMA_DIR.exists():
        print(f"Schema directory not found: {SCHEMA_DIR}")
        return 1

    if not EXAMPLE_DIR.exists():
        print(f"Example directory not found: {EXAMPLE_DIR}")
        return 1

    failed |= validate_schemas()
    failed |= validate_examples()

    print("\nChecking schema/example pairs...")
    failed |= check_pair_counts()

    if failed:
        print("\nContract validation FAILED.")
        return 1

    print("\nAll Contract v1.1 schemas and examples are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
