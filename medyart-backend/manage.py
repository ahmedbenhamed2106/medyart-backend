#!/usr/bin/env python
import os
import sys
from pathlib import Path

def main():
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR / 'medyart'))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medyart.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
