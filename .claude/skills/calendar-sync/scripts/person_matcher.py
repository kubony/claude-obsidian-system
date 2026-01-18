#!/usr/bin/env python3
"""
Person Matcher

Match calendar event attendees to person directory files.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional

VAULT_PATH = Path("/path/to/vault")
PERSON_DIR = VAULT_PATH / "04_Networking/00_인물사전"

# 직급/직책 단어 (이름 매칭에서 제외)
EXCLUDE_WORDS = {
    # 직급
    '회장', '부회장', '사장', '부사장', '전무', '상무', '이사',
    '부장', '차장', '과장', '대리', '사원', '주임', '책임',
    '수석', '선임', '연구원', '매니저', '파트장', '실장', '본부장',
    '팀장', '팀원', '센터장', '소장', '원장', '국장', '처장',
    # 직책/역할
    '대표', '대표님', '교수', '교수님', '박사', '석사', '님',
    '선생', '선생님', '강사', '코치', '멘토', '멘티',
    # 일반 단어
    '미팅', '회의', '통화', '식사', '점심', '저녁', '커피', '챗',
    '온라인', '오프라인', '줌', '구글', '화상', '전화',
    '집들이', '모임', '행사', '세미나', '워크샵',
}


class PersonMatcher:
    """
    Match calendar event data to person directory files.

    Builds an index of all persons in the directory for efficient lookup.
    """

    def __init__(self, person_dir: Path = PERSON_DIR):
        self.person_dir = person_dir
        self.email_index: Dict[str, Path] = {}
        self.name_index: Dict[str, Path] = {}
        self._build_index()

    def _parse_yaml_frontmatter(self, content: str) -> Dict:
        """Extract YAML frontmatter from markdown content."""
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            try:
                return yaml.safe_load(match.group(1)) or {}
            except yaml.YAMLError:
                return {}
        return {}

    def _build_index(self):
        """Build lookup indices for email and name."""
        if not self.person_dir.exists():
            return

        for md_file in self.person_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding='utf-8')
                metadata = self._parse_yaml_frontmatter(content)

                # Index by email
                contact = metadata.get('contact', {})
                if isinstance(contact, dict):
                    email = contact.get('email')
                    if email:
                        self.email_index[email.lower()] = md_file

                # Index by name from filename (이름_소속.md)
                name = md_file.stem.split('_')[0]
                if name and len(name) >= 2:
                    self.name_index[name] = md_file

                # Index by title
                title = metadata.get('title', '')
                if title:
                    # Korean name
                    self.name_index[title] = md_file
                    # English name in parentheses
                    eng_match = re.search(r'\(([^)]+)\)', title)
                    if eng_match:
                        eng_name = eng_match.group(1).strip()
                        self.name_index[eng_name.lower()] = md_file

            except Exception:
                continue

    def find_by_email(self, email: str) -> Optional[Path]:
        """Find person file by email address."""
        if not email:
            return None
        return self.email_index.get(email.lower())

    def find_by_name(self, name: str) -> Optional[Path]:
        """Find person file by name."""
        if not name or len(name) < 2:
            return None

        # Exact match
        if name in self.name_index:
            return self.name_index[name]

        # Case-insensitive match
        name_lower = name.lower()
        if name_lower in self.name_index:
            return self.name_index[name_lower]

        # Partial match
        for indexed_name, file_path in self.name_index.items():
            indexed_lower = indexed_name.lower()
            if name_lower in indexed_lower or indexed_lower in name_lower:
                return file_path

        return None

    def match_event(self, event: Dict) -> List[Dict]:
        """
        Match a calendar event to person files.

        Args:
            event: Calendar event dictionary with keys like 'attendees', 'summary'.

        Returns:
            List of dictionaries with match info:
            [{'file_path': Path, 'match_type': str, 'match_value': str}, ...]
        """
        matches = []
        seen_paths = set()

        # 1. Match by attendee email
        for attendee in event.get('attendees', []):
            email = attendee.get('email', '')
            if email and not email.endswith('calendar.google.com'):
                file_path = self.find_by_email(email)
                if file_path and file_path not in seen_paths:
                    matches.append({
                        'file_path': file_path,
                        'match_type': 'email',
                        'match_value': email
                    })
                    seen_paths.add(file_path)

        # 2. Match by name in summary (title)
        summary = event.get('summary', '')
        if summary:
            # Extract potential names (Korean: 2-4 chars, or words before 님)
            potential_names = []

            # Pattern: "조쉬님", "김민주님"
            nim_pattern = r'([가-힣A-Za-z]{2,10})님'
            nim_matches = re.findall(nim_pattern, summary)
            potential_names.extend(nim_matches)

            # Pattern: Korean names (2-4 chars)
            korean_pattern = r'([가-힣]{2,4})'
            korean_matches = re.findall(korean_pattern, summary)
            potential_names.extend(korean_matches)

            # Filter out excluded words (직급, 일반 단어 등)
            potential_names = [n for n in potential_names if n not in EXCLUDE_WORDS]

            for name in potential_names:
                file_path = self.find_by_name(name)
                if file_path and file_path not in seen_paths:
                    matches.append({
                        'file_path': file_path,
                        'match_type': 'name',
                        'match_value': name
                    })
                    seen_paths.add(file_path)

        return matches

    def get_person_info(self, file_path: Path) -> Dict:
        """Get basic info from a person file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            metadata = self._parse_yaml_frontmatter(content)

            name = metadata.get('title', file_path.stem.split('_')[0])
            org = file_path.stem.split('_')[1] if '_' in file_path.stem else ''

            contact = metadata.get('contact', {})
            if not isinstance(contact, dict):
                contact = {}

            return {
                'name': name,
                'org': org,
                'email': contact.get('email'),
                'phone': contact.get('phone'),
                'file_path': str(file_path),
            }
        except Exception:
            return {
                'name': file_path.stem.split('_')[0],
                'file_path': str(file_path),
            }


def main():
    """Test the person matcher."""
    matcher = PersonMatcher()

    print(f"인물사전 인덱스 구축 완료")
    print(f"  이메일 인덱스: {len(matcher.email_index)}개")
    print(f"  이름 인덱스: {len(matcher.name_index)}개")

    # Test event matching
    test_event = {
        'summary': '조쉬님 커피챗',
        'attendees': [
            {'email': 'attendee@example.com'},
            {'email': 'test@example.com'},
        ]
    }

    print(f"\n테스트 이벤트: {test_event['summary']}")
    matches = matcher.match_event(test_event)

    if matches:
        print(f"매칭 결과: {len(matches)}개")
        for m in matches:
            print(f"  - {m['file_path'].name} ({m['match_type']}: {m['match_value']})")
    else:
        print("매칭 없음")


if __name__ == "__main__":
    main()
