#!/usr/bin/env python3
"""
Person Directory Lookup

Lookup person information from the Obsidian vault person directory.
"""

import re
import yaml
from pathlib import Path
from typing import Optional, Dict

VAULT_PATH = Path("/Users/inkeun/projects/obsidian")
PERSON_DIR = VAULT_PATH / "04_Networking/00_인물사전"


def parse_yaml_frontmatter(content: str) -> Dict:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}
    return {}


def find_person_file(name: str) -> Optional[Path]:
    """
    Find a person file by name.

    Search order:
    1. Exact filename match (이름_소속.md)
    2. Partial filename match
    3. YAML title match
    """
    if not PERSON_DIR.exists():
        return None

    # Normalize search name
    search_name = name.strip().lower()

    # 1. Exact filename match
    for md_file in PERSON_DIR.glob("*.md"):
        file_name = md_file.stem.split('_')[0].lower()
        if file_name == search_name:
            return md_file

    # 2. Partial filename match
    for md_file in PERSON_DIR.glob("*.md"):
        file_name = md_file.stem.split('_')[0].lower()
        if search_name in file_name or file_name in search_name:
            return md_file

    # 3. YAML title match
    for md_file in PERSON_DIR.glob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8')
            metadata = parse_yaml_frontmatter(content)
            title = metadata.get('title', '').lower()
            if search_name in title:
                return md_file
        except Exception:
            continue

    return None


def get_person_email(name: str) -> Optional[str]:
    """
    Get email address for a person by name.

    Args:
        name: Person name to search for.

    Returns:
        Email address if found, None otherwise.
    """
    file_path = find_person_file(name)
    if not file_path:
        return None

    try:
        content = file_path.read_text(encoding='utf-8')
        metadata = parse_yaml_frontmatter(content)

        # Check YAML contact structure
        contact = metadata.get('contact', {})
        if isinstance(contact, dict):
            email = contact.get('email')
            if email:
                return email

        # Fallback: search in body
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        matches = re.findall(email_pattern, content)
        if matches:
            return matches[0]

    except Exception:
        pass

    return None


def get_person_info(name: str) -> Optional[Dict]:
    """
    Get full person information by name.

    Args:
        name: Person name to search for.

    Returns:
        Dictionary with person info or None if not found.
    """
    file_path = find_person_file(name)
    if not file_path:
        return None

    try:
        content = file_path.read_text(encoding='utf-8')
        metadata = parse_yaml_frontmatter(content)

        # Extract name from filename
        file_name = file_path.stem.split('_')[0]
        org = file_path.stem.split('_')[1] if '_' in file_path.stem else ''

        # Contact info
        contact = metadata.get('contact', {})
        if not isinstance(contact, dict):
            contact = {}

        return {
            'name': metadata.get('title', file_name),
            'file_path': str(file_path),
            'organization': org,
            'email': contact.get('email'),
            'phone': contact.get('phone'),
            'tags': metadata.get('tags', []),
            'summary': metadata.get('summary', ''),
        }

    except Exception:
        return None


def list_all_persons() -> list:
    """
    List all persons in the directory.

    Returns:
        List of (name, file_path) tuples.
    """
    if not PERSON_DIR.exists():
        return []

    persons = []
    for md_file in PERSON_DIR.glob("*.md"):
        name = md_file.stem.split('_')[0]
        persons.append((name, md_file))

    return sorted(persons, key=lambda x: x[0])


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python person_lookup.py <name>")
        print("\nExample: python person_lookup.py 조쉬")
        sys.exit(1)

    name = sys.argv[1]
    info = get_person_info(name)

    if info:
        print(f"✅ {info['name']} 정보 찾음")
        print(f"   파일: {info['file_path']}")
        if info['email']:
            print(f"   이메일: {info['email']}")
        if info['phone']:
            print(f"   전화: {info['phone']}")
        if info['organization']:
            print(f"   소속: {info['organization']}")
    else:
        print(f"❌ '{name}'을 찾을 수 없습니다.")
