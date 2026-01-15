#!/usr/bin/env python3
"""
Obsidian Vault → RDF/TTL 변환 스크립트

인물사전 및 프로젝트 폴더의 마크다운 파일을 분석하여 RDF 트리플로 변환합니다.

대상 폴더:
- 04_Networking/00_인물사전/ (Person)
- 00_A_Projects/ (Project)
- 90_Archives/ (Project, archived)

Usage:
    python vault_to_ttl.py <vault_path> [--output <output.ttl>]

Example:
    python vault_to_ttl.py /path/to/obsidian --output knowledge.ttl
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path
from datetime import datetime
from urllib.parse import quote


def normalize_str(s: str) -> str:
    """macOS NFD → NFC 정규화"""
    return unicodedata.normalize('NFC', s)

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, XSD
except ImportError:
    print("Error: rdflib required. Install with: pip install rdflib")
    sys.exit(1)


# Namespaces
ONT = Namespace("http://obsidian.local/ontology#")
DATA = Namespace("http://obsidian.local/data#")


def sanitize_uri(name: str) -> str:
    """이름을 URI-safe 문자열로 변환"""
    # 공백과 특수문자 처리
    safe = re.sub(r'[^\w가-힣]', '_', name)
    return quote(safe, safe='')


def parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """YAML front matter와 본문 분리"""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        metadata = yaml.safe_load(parts[1]) or {}
        body = parts[2].strip()
        return metadata, body
    except yaml.YAMLError:
        return {}, content


def extract_meetings(body: str) -> list[dict]:
    """본문에서 미팅 섹션 추출 (다양한 날짜 패턴 지원)"""
    meetings = []
    seen_dates = set()  # 중복 방지

    # 1. 헤딩 기반 패턴 (## 또는 ### 레벨)
    heading_patterns = [
        (r'#{2,3}\s*(\d{4})\.(\d{2})\.(\d{2})\s*(.*?)(?=\n#{1,3}\s|\n---|\Z)', 'full'),  # 2024.11.21
        (r'#{2,3}\s*(\d{4})-(\d{2})-(\d{2})\s*(.*?)(?=\n#{1,3}\s|\n---|\Z)', 'full'),     # 2024-11-21
        (r'#{2,3}\s*(\d{2})(\d{2})(\d{2})\s*(.*?)(?=\n#{1,3}\s|\n---|\Z)', 'short'),       # 241121 (YYMMDD)
        (r'#{2,3}\s*(\d{4})\.(\d{2})\s+(.*?)(?=\n#{1,3}\s|\n---|\Z)', 'month'),            # 2024.12 제목
        (r'#{2,3}\s*(\d{4})-(\d{2})\s+(.*?)(?=\n#{1,3}\s|\n---|\Z)', 'month'),             # 2024-12 제목
    ]

    # 2. 불릿 포인트 기반 패턴 (- YYYY.MM.DD 형식)
    bullet_patterns = [
        (r'^-\s*(\d{4})\.(\d{2})\.(\d{2})\s+(.+?)$', 'full'),    # - 2024.11.21 내용
        (r'^-\s*(\d{4})-(\d{2})-(\d{2})\s+(.+?)$', 'full'),      # - 2024-11-21 내용
        (r'^-\s*(\d{4})\.(\d{2})\s+(.+?)$', 'month'),            # - 2024.12 내용
        (r'^-\s*(\d{4})-(\d{2})\s+(.+?)$', 'month'),             # - 2024-12 내용
    ]

    def parse_date_groups(groups, fmt):
        """날짜 그룹 파싱"""
        try:
            if fmt == 'short':  # YYMMDD format
                year = f"20{groups[0]}"
                month, day = groups[1], groups[2]
                content = groups[3].strip() if len(groups) > 3 else ""
            elif fmt == 'month':  # YYYY.MM format (day defaults to 01)
                year = groups[0]
                month = groups[1]
                day = "01"
                content = groups[2].strip() if len(groups) > 2 else ""
            else:  # full date
                year = groups[0]
                month, day = groups[1], groups[2]
                content = groups[3].strip() if len(groups) > 3 else ""

            date = datetime.strptime(f"{year}-{month}-{day}", "%Y-%m-%d").date()
            return date, content
        except ValueError:
            return None, None

    # 헤딩 기반 미팅 추출
    for pattern, fmt in heading_patterns:
        for match in re.finditer(pattern, body, re.DOTALL):
            date, content = parse_date_groups(match.groups(), fmt)
            if date and str(date) not in seen_dates:
                seen_dates.add(str(date))
                meetings.append({'date': date, 'content': content})

    # 불릿 기반 미팅 추출 (멀티라인 모드)
    for pattern, fmt in bullet_patterns:
        for match in re.finditer(pattern, body, re.MULTILINE):
            date, content = parse_date_groups(match.groups(), fmt)
            if date and str(date) not in seen_dates:
                seen_dates.add(str(date))
                meetings.append({'date': date, 'content': content})

    return meetings


def extract_topics_from_content(content: str) -> list[str]:
    """미팅 내용에서 주요 주제 추출"""
    topics = []

    # 해시태그 추출
    hashtags = re.findall(r'#(\w+)', content)
    topics.extend(hashtags)

    # 키워드 패턴 (주요 키워드들)
    keyword_patterns = [
        r'(?:투자|펀딩|시리즈)',
        r'(?:창업|스타트업|사업)',
        r'(?:채용|이직|면접)',
        r'(?:기술|개발|AI|ML)',
        r'(?:네트워킹|커피챗|미팅)',
    ]

    for pattern in keyword_patterns:
        if re.search(pattern, content):
            match = re.search(pattern, content)
            if match:
                topics.append(match.group())

    return list(set(topics))


def extract_wiki_links(content: str) -> list[str]:
    """[[링크]] 패턴에서 연결된 노트 추출"""
    return re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)


def parse_project_folder_name(folder_name: str) -> dict:
    """프로젝트 폴더명에서 이름과 날짜 추출

    예시:
    - "2509 AI영정사진" → name: "AI영정사진", date: 2025-09-01
    - "251218 볼드 해커톤" → name: "볼드 해커톤", date: 2025-12-18
    - "Mr.Trend" → name: "Mr.Trend", date: None
    """
    # YYMMDD 형식 (예: 251218 볼드 해커톤)
    match = re.match(r'^(\d{6})\s+(.+)$', folder_name)
    if match:
        date_str, name = match.groups()
        try:
            date = datetime.strptime(f"20{date_str}", "%Y%m%d").date()
            return {'name': name, 'date': date}
        except ValueError:
            pass

    # YYMM 형식 (예: 2509 AI영정사진)
    match = re.match(r'^(\d{4})\s+(.+)$', folder_name)
    if match:
        date_str, name = match.groups()
        try:
            date = datetime.strptime(f"20{date_str}01", "%Y%m%d").date()
            return {'name': name, 'date': date}
        except ValueError:
            pass

    # 날짜 없는 경우
    return {'name': folder_name, 'date': None}


def parse_project_file(file_path: Path, project_name: str) -> dict:
    """프로젝트 내 파일 파싱"""
    content = file_path.read_text(encoding='utf-8')
    metadata, body = parse_yaml_frontmatter(content)

    # YAML에서 정보 추출
    title = metadata.get('title', file_path.stem)
    tags = metadata.get('tags', [])
    summary = metadata.get('summary', '')
    date = metadata.get('date')

    # 미팅/로그 추출
    meetings = extract_meetings(body)

    # 위키링크 추출
    links = extract_wiki_links(body)

    return {
        'title': title,
        'project': project_name,
        'tags': tags if isinstance(tags, list) else [tags],
        'summary': summary,
        'date': date,
        'meetings': meetings,
        'links': links,
        'file_path': str(file_path),
    }


def parse_person_file(file_path: Path) -> dict:
    """인물사전 파일 파싱"""
    content = file_path.read_text(encoding='utf-8')
    metadata, body = parse_yaml_frontmatter(content)

    # 파일명에서 이름과 소속 추출 (이름_소속.md 형식)
    stem = file_path.stem
    parts = stem.rsplit('_', 1)
    name = parts[0]
    affiliation = parts[1] if len(parts) > 1 else None

    # YAML에서 정보 추출
    title = metadata.get('title', name)
    tags = metadata.get('tags', [])
    summary = metadata.get('summary', '')
    date = metadata.get('date')
    contact = metadata.get('contact', {})
    last_contact = metadata.get('last_contact')

    # 미팅 추출
    meetings = extract_meetings(body)

    # 위키링크 추출
    links = extract_wiki_links(body)

    return {
        'name': title or name,
        'affiliation': affiliation,
        'tags': tags if isinstance(tags, list) else [tags],
        'summary': summary,
        'date': date,
        'contact': contact if isinstance(contact, dict) else {},
        'last_contact': last_contact,
        'meetings': meetings,
        'links': links,
        'file_path': str(file_path),
    }


def build_graph(vault_path: Path) -> Graph:
    """볼트에서 RDF 그래프 생성"""
    g = Graph()
    g.bind('', ONT)
    g.bind('data', DATA)
    g.bind('rdf', RDF)
    g.bind('rdfs', RDFS)
    g.bind('xsd', XSD)

    organizations = set()
    all_persons = {}
    all_projects = {}
    meeting_count = 0

    # =========================================================================
    # 1. 인물사전 처리
    # =========================================================================
    person_dir = vault_path / '04_Networking' / '00_인물사전'

    if person_dir.exists():
        person_files = list(person_dir.glob('*.md'))
        print(f"인물사전 파일: {len(person_files)}개")

        for file_path in person_files:
            data = parse_person_file(file_path)
            person_uri = DATA[sanitize_uri(data['name'])]
            all_persons[data['name']] = person_uri

            # Person 트리플
            g.add((person_uri, RDF.type, ONT.Person))
            g.add((person_uri, ONT.name, Literal(data['name'], lang='ko')))
            g.add((person_uri, ONT.filePath, Literal(data['file_path'])))

            if data['summary']:
                g.add((person_uri, ONT.summary, Literal(data['summary'], lang='ko')))

            # 연락처 처리
            if data['contact']:
                contact = data['contact']
                if contact.get('phone'):
                    g.add((person_uri, ONT.hasPhone, Literal(contact['phone'])))
                if contact.get('email'):
                    g.add((person_uri, ONT.hasEmail, Literal(contact['email'])))
                if contact.get('linkedin'):
                    g.add((person_uri, ONT.hasLinkedIn, Literal(contact['linkedin'])))
                if contact.get('slack'):
                    g.add((person_uri, ONT.hasSlack, Literal(contact['slack'])))
                if contact.get('discord'):
                    g.add((person_uri, ONT.hasDiscord, Literal(contact['discord'])))
                if contact.get('kakao'):
                    g.add((person_uri, ONT.hasKakao, Literal(contact['kakao'])))
                if contact.get('instagram'):
                    g.add((person_uri, ONT.hasInstagram, Literal(contact['instagram'])))
                if contact.get('twitter'):
                    g.add((person_uri, ONT.hasTwitter, Literal(contact['twitter'])))
                if contact.get('github'):
                    g.add((person_uri, ONT.hasGitHub, Literal(contact['github'])))
                if contact.get('website'):
                    g.add((person_uri, ONT.hasWebsite, Literal(contact['website'])))

            # 마지막 연락일 처리
            if data.get('last_contact'):
                try:
                    # YYYY-MM-DD 형식 검증 후 xsd:date로 추가
                    date_obj = datetime.strptime(data['last_contact'], '%Y-%m-%d')
                    g.add((person_uri, ONT.hasLastContact, Literal(data['last_contact'], datatype=XSD.date)))
                except (ValueError, TypeError):
                    # 날짜 형식이 잘못된 경우 문자열로 저장
                    g.add((person_uri, ONT.hasLastContact, Literal(str(data['last_contact']))))

            # 소속 처리
            if data['affiliation']:
                org_uri = DATA[sanitize_uri(data['affiliation'])]
                if data['affiliation'] not in organizations:
                    g.add((org_uri, RDF.type, ONT.Organization))
                    g.add((org_uri, ONT.name, Literal(data['affiliation'], lang='ko')))
                    organizations.add(data['affiliation'])
                g.add((person_uri, ONT.affiliatedWith, org_uri))

            # 태그 처리
            for tag in data['tags']:
                if tag:
                    g.add((person_uri, ONT.tag, Literal(str(tag), lang='ko')))

            # 미팅 처리
            for i, meeting in enumerate(data['meetings']):
                meeting_id = f"{sanitize_uri(data['name'])}_meeting_{i}"
                meeting_uri = DATA[meeting_id]

                g.add((meeting_uri, RDF.type, ONT.Meeting))
                g.add((meeting_uri, ONT.participant, person_uri))
                g.add((meeting_uri, ONT.date, Literal(meeting['date'], datatype=XSD.date)))

                if meeting['content']:
                    g.add((meeting_uri, ONT.summary, Literal(meeting['content'][:500], lang='ko')))

                    # 주제 추출
                    topics = extract_topics_from_content(meeting['content'])
                    for topic in topics:
                        topic_uri = DATA[sanitize_uri(topic)]
                        g.add((topic_uri, RDF.type, ONT.Topic))
                        g.add((topic_uri, ONT.name, Literal(topic, lang='ko')))
                        g.add((meeting_uri, ONT.hasTopic, topic_uri))

                meeting_count += 1

        # 인물 간 링크 처리
        for file_path in person_files:
            data = parse_person_file(file_path)
            person_uri = all_persons.get(data['name'])

            if person_uri:
                for link in data['links']:
                    linked_person = all_persons.get(link)
                    if linked_person and linked_person != person_uri:
                        g.add((person_uri, ONT.knows, linked_person))
    else:
        print(f"Warning: 인물사전 폴더를 찾을 수 없습니다: {person_dir}")

    # =========================================================================
    # 2. 프로젝트 폴더 처리 (00_A_Projects, 90_Archives)
    # =========================================================================
    project_dirs = [
        (vault_path / '00_A_Projects' / 'Active', False),
        (vault_path / '00_A_Projects' / 'Planning', False),
        (vault_path / '90_Archives', True),
    ]

    for project_base, is_archived in project_dirs:
        if not project_base.exists():
            continue

        # 하위 폴더들이 각각 프로젝트
        for project_folder in project_base.iterdir():
            if not project_folder.is_dir():
                # 루트의 .md 파일은 건너뜀
                continue
            if project_folder.name.startswith('.'):
                continue

            # 폴더명 Unicode 정규화 (macOS NFD → NFC)
            folder_name = normalize_str(project_folder.name)

            # 폴더명에서 프로젝트 정보 추출
            proj_info = parse_project_folder_name(folder_name)
            project_name = proj_info['name']
            project_date = proj_info['date']

            # Project 엔티티 생성
            project_uri = DATA[f"project_{sanitize_uri(folder_name)}"]
            all_projects[folder_name] = project_uri

            g.add((project_uri, RDF.type, ONT.Project))
            g.add((project_uri, ONT.name, Literal(project_name, lang='ko')))
            g.add((project_uri, ONT.filePath, Literal(str(project_folder))))

            if project_date:
                g.add((project_uri, ONT.date, Literal(project_date, datatype=XSD.date)))

            if is_archived:
                g.add((project_uri, ONT.tag, Literal('archived', lang='en')))

            # 프로젝트 내 모든 md 파일 처리
            project_files = list(project_folder.rglob('*.md'))

            for file_path in project_files:
                try:
                    file_data = parse_project_file(file_path, project_name)
                except Exception as e:
                    print(f"Warning: 파일 처리 실패 {file_path}: {e}")
                    continue

                # 파일의 태그를 프로젝트에 추가
                for tag in file_data['tags']:
                    if tag:
                        g.add((project_uri, ONT.tag, Literal(str(tag), lang='ko')))

                # 파일의 summary가 있으면 프로젝트 summary로 (첫 번째만)
                if file_data['summary'] and not list(g.objects(project_uri, ONT.summary)):
                    g.add((project_uri, ONT.summary, Literal(file_data['summary'], lang='ko')))

                # 미팅/로그 추출
                for i, meeting in enumerate(file_data['meetings']):
                    meeting_id = f"project_{sanitize_uri(folder_name)}_meeting_{meeting_count}"
                    meeting_uri = DATA[meeting_id]

                    g.add((meeting_uri, RDF.type, ONT.Meeting))
                    g.add((meeting_uri, ONT.date, Literal(meeting['date'], datatype=XSD.date)))
                    g.add((meeting_uri, ONT.relatedTo, project_uri))

                    if meeting['content']:
                        g.add((meeting_uri, ONT.summary, Literal(meeting['content'][:500], lang='ko')))

                        # 주제 추출
                        topics = extract_topics_from_content(meeting['content'])
                        for topic in topics:
                            topic_uri = DATA[sanitize_uri(topic)]
                            g.add((topic_uri, RDF.type, ONT.Topic))
                            g.add((topic_uri, ONT.name, Literal(topic, lang='ko')))
                            g.add((meeting_uri, ONT.hasTopic, topic_uri))

                    meeting_count += 1

                # 위키링크에서 인물 연결
                for link in file_data['links']:
                    if link in all_persons:
                        g.add((all_persons[link], ONT.involvedIn, project_uri))

    print(f"프로젝트: {len(all_projects)}개")
    print(f"총 미팅/로그: {meeting_count}개")

    return g


def main():
    parser = argparse.ArgumentParser(
        description='Obsidian 볼트를 RDF/TTL로 변환'
    )
    parser.add_argument('vault_path', help='Obsidian 볼트 경로')
    parser.add_argument('--output', '-o', default='knowledge.ttl',
                        help='출력 파일 경로 (기본: knowledge.ttl)')

    args = parser.parse_args()
    vault_path = Path(args.vault_path)

    if not vault_path.exists():
        print(f"Error: 볼트 경로를 찾을 수 없습니다: {vault_path}")
        sys.exit(1)

    print(f"볼트 변환 시작: {vault_path}")

    graph = build_graph(vault_path)

    # TTL 파일로 저장
    output_path = Path(args.output)
    graph.serialize(destination=str(output_path), format='turtle')

    # 통계 출력
    print(f"\n변환 완료!")
    print(f"  - 총 트리플 수: {len(graph)}")
    print(f"  - 출력 파일: {output_path}")

    # 클래스별 개수
    for cls_name in ['Person', 'Project', 'Meeting', 'Organization', 'Topic']:
        cls_uri = ONT[cls_name]
        count = len(list(graph.subjects(RDF.type, cls_uri)))
        print(f"  - {cls_name}: {count}개")


if __name__ == '__main__':
    main()
