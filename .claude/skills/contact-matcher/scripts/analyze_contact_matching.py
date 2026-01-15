#!/usr/bin/env python3
"""
연락처 매칭 분석 - VCF 및 Google CSV 지원
"""

import re
import csv
from pathlib import Path
from typing import Dict, List, Set
import unicodedata

def normalize_str(s: str) -> str:
    """macOS NFD → NFC 정규화"""
    return unicodedata.normalize('NFC', s)

def parse_vcf_file(vcf_path: Path) -> List[Dict]:
    """VCF 파일 파싱"""
    contacts = []
    current_contact = {}

    with open(vcf_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if line == 'BEGIN:VCARD':
                current_contact = {}
            elif line == 'END:VCARD':
                if current_contact:
                    contacts.append(current_contact)
            elif ':' in line:
                # FN (Full Name)
                if line.startswith('FN:'):
                    current_contact['name'] = line.split(':', 1)[1].strip()

                # N (Structured Name: 성;이름)
                elif line.startswith('N:'):
                    parts = line.split(':', 1)[1].split(';')
                    if len(parts) >= 2:
                        surname = parts[0].strip()
                        given = parts[1].strip()
                        if surname and given:
                            current_contact['structured_name'] = f"{surname}{given}"
                        elif given:
                            current_contact['structured_name'] = given

                # ORG (Organization)
                elif line.startswith('ORG:'):
                    org = line.split(':', 1)[1].split(';')[0].strip()
                    if org:
                        current_contact['org'] = org

                # EMAIL
                elif line.startswith('EMAIL'):
                    email = line.split(':', 1)[1].strip()
                    if 'email' not in current_contact:
                        current_contact['email'] = email

                # TEL
                elif line.startswith('TEL'):
                    phone = line.split(':', 1)[1].strip()
                    phone = re.sub(r'(\d{3})(\d{4})(\d{4})', r'\1-\2-\3', phone.replace('-', ''))
                    if 'phone' not in current_contact:
                        current_contact['phone'] = phone

    return contacts


def parse_csv_file(csv_path: Path) -> List[Dict]:
    """Google Contacts CSV 파일 파싱"""
    contacts = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            contact = {}

            # 이름 조합 (First Name + Last Name 또는 File As 사용)
            first_name = row.get('First Name', '').strip()
            last_name = row.get('Last Name', '').strip()
            file_as = row.get('File As', '').strip()

            # 특수문자 제거 (예: "#정사은 대표" → "정사은 대표")
            first_name = first_name.lstrip('#')
            last_name = last_name.lstrip('#')

            # First Name이 그룹 정보(예: "5기", "1기")인 경우 무시
            if first_name and (re.match(r'^\d+기$', first_name) or first_name.isdigit()):
                first_name = ''

            # 한글 이름 (First Name이 한글인 경우)
            if first_name:
                if last_name:
                    # Last Name + First Name 순서로 조합
                    contact['structured_name'] = f"{last_name}{first_name}"
                    contact['name'] = f"{last_name}{first_name}"
                else:
                    contact['structured_name'] = first_name
                    contact['name'] = first_name
            elif last_name:
                # First Name 없고 Last Name만 있는 경우
                contact['structured_name'] = last_name
                contact['name'] = last_name
            elif file_as:
                contact['structured_name'] = file_as
                contact['name'] = file_as

            # 조직
            org = row.get('Organization Name', '').strip()
            if org:
                contact['org'] = org

            # 전화번호 (Phone 1~4 중 첫 번째 찾기)
            for i in range(1, 5):
                phone = row.get(f'Phone {i} - Value', '').strip()
                if phone:
                    # 국제 형식 처리 (+82 → 0)
                    phone = re.sub(r'^\+82[\s-]?', '0', phone)
                    # 모든 공백, 하이픈, 괄호 제거
                    phone = re.sub(r'[\s\-\(\)]', '', phone)
                    # 숫자만 추출
                    phone = re.sub(r'[^\d]', '', phone)
                    # 11자리 숫자인 경우에만 포맷팅 (010XXXXXXXX → 010-XXXX-XXXX)
                    if len(phone) == 11 and phone.startswith('010'):
                        phone = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                        contact['phone'] = phone
                        break
                    elif len(phone) == 10 and phone.startswith('0'):
                        # 10자리 (지역번호)
                        phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                        contact['phone'] = phone
                        break

            # 이메일 (E-mail 1~3 중 첫 번째 찾기)
            for i in range(1, 4):
                email = row.get(f'E-mail {i} - Value', '').strip()
                if email:
                    contact['email'] = email
                    break

            # 연락처 정보가 있는 것만 추가
            if contact.get('name') or contact.get('phone') or contact.get('email'):
                contacts.append(contact)

    return contacts


def extract_person_info(file_path: Path) -> Dict:
    """인물사전 파일에서 정보 추출"""
    filename = file_path.name.replace('.md', '')

    # 파일명 분석: 이름_소속.md
    parts = filename.split('_', 1)
    name = parts[0]
    org = parts[1] if len(parts) > 1 else ''

    # YAML에서 추가 정보 추출
    content = file_path.read_text(encoding='utf-8')
    content = normalize_str(content)

    # 이메일 추출 (contact 필드에서)
    email_match = re.search(r'email:\s*(\S+@\S+)', content)
    email = email_match.group(1) if email_match and email_match.group(1) != 'null' else None

    # 전화번호 추출
    phone_match = re.search(r'phone:\s*(\d{2,3}-\d{3,4}-\d{4})', content)
    phone = phone_match.group(1) if phone_match else None

    return {
        'file_path': file_path,
        'name': name,
        'org': org,
        'email': email,
        'phone': phone,
    }

def find_potential_matches(person: Dict, contacts: List[Dict]) -> List[Dict]:
    """다양한 방식으로 잠재적 매칭 찾기"""
    matches = []

    person_name = normalize_str(person['name']).strip()
    person_org = normalize_str(person['org']).strip()

    for contact in contacts:
        match_score = 0
        match_reasons = []

        # 이름 매칭
        contact_name = contact.get('structured_name') or contact.get('name', '')
        contact_name = normalize_str(contact_name).strip()

        # 불필요한 텍스트 제거
        contact_name_clean = re.sub(r'\d{8}', '', contact_name)
        contact_name_clean = re.sub(r'(연구원|대리|선임|책임|과장|부장|이사|사원|팀장|매니저|대표|본부장)\s*', '', contact_name_clean)
        contact_name_clean = contact_name_clean.strip()

        # 빈 이름은 스킵 (중요: 빈 문자열은 모든 문자열에 포함되므로)
        if not contact_name_clean or len(contact_name_clean) < 2:
            continue

        # 1. 정확한 이름 일치
        if contact_name_clean == person_name:
            match_score += 10
            match_reasons.append('이름 정확 일치')
        # 2. 이름이 포함됨 (최소 길이 체크로 오매칭 방지)
        elif len(contact_name_clean) >= 2 and len(person_name) >= 2:
            if person_name in contact_name_clean or contact_name_clean in person_name:
                match_score += 7
                match_reasons.append('이름 부분 일치')
        # 3. 성만 일치 (2글자 이상인 경우)
        elif len(person_name) >= 2 and len(contact_name_clean) >= 2 and person_name[0] == contact_name_clean[0]:
            match_score += 2
            match_reasons.append('성 일치')

        # 소속 매칭
        contact_org = contact.get('org', '')
        contact_org = normalize_str(contact_org).strip()

        if person_org and contact_org:
            # 정확한 소속 일치
            if person_org == contact_org:
                match_score += 8
                match_reasons.append('소속 정확 일치')
            # 소속 부분 일치
            elif person_org in contact_org or contact_org in person_org:
                match_score += 5
                match_reasons.append('소속 부분 일치')

        # 이메일 매칭
        if person['email'] and contact.get('email'):
            if person['email'] == contact['email']:
                match_score += 15
                match_reasons.append('이메일 일치')
            # 이메일 도메인과 소속 비교
            else:
                person_domain = person['email'].split('@')[1] if '@' in person['email'] else ''
                contact_domain = contact['email'].split('@')[1] if '@' in contact['email'] else ''
                if person_domain and contact_domain and person_domain == contact_domain:
                    match_score += 3
                    match_reasons.append('이메일 도메인 일치')

        # 전화번호 매칭
        if person['phone'] and contact.get('phone'):
            if person['phone'] == contact['phone']:
                match_score += 15
                match_reasons.append('전화번호 일치')

        # 매칭 점수가 있으면 추가
        if match_score > 0:
            matches.append({
                'contact': contact,
                'score': match_score,
                'reasons': match_reasons,
            })

    # 점수순으로 정렬
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='연락처와 인물사전 매칭 분석 (VCF/CSV 지원)')
    parser.add_argument('--contact-file', required=True, help='연락처 파일 경로 (VCF 또는 CSV)')
    parser.add_argument('--vcf', help='[호환성] VCF 파일 경로 (--contact-file 대신 사용 가능)')
    parser.add_argument('--person-dir', required=True, help='인물사전 디렉토리 경로')
    parser.add_argument('--min-score', type=int, default=7, help='최소 매칭 점수 (기본값: 7)')
    parser.add_argument('--limit', type=int, default=30, help='출력할 최대 결과 수 (기본값: 30)')

    args = parser.parse_args()

    # 호환성: --vcf 옵션 지원
    contact_file = args.contact_file or args.vcf
    if not contact_file:
        print("Error: --contact-file 또는 --vcf 옵션이 필요합니다.")
        sys.exit(1)

    contact_path = Path(contact_file)
    person_dir = Path(args.person_dir)

    if not contact_path.exists():
        print(f"Error: 연락처 파일을 찾을 수 없습니다: {contact_path}")
        sys.exit(1)

    if not person_dir.exists():
        print(f"Error: 인물사전 디렉토리를 찾을 수 없습니다: {person_dir}")
        sys.exit(1)

    # 파일 형식 감지
    file_ext = contact_path.suffix.lower()

    if file_ext == '.vcf':
        print("VCF 파일 파싱 중...")
        contacts = parse_vcf_file(contact_path)
    elif file_ext == '.csv':
        print("Google CSV 파일 파싱 중...")
        contacts = parse_csv_file(contact_path)
    else:
        print(f"Error: 지원하지 않는 파일 형식입니다: {file_ext}")
        print("VCF 또는 CSV 파일을 사용하세요.")
        sys.exit(1)

    print(f"총 {len(contacts)}개 연락처 발견\n")

    print("인물사전 파일 분석 중...")
    person_files = sorted(person_dir.glob('*.md'))
    persons = [extract_person_info(f) for f in person_files]
    print(f"총 {len(persons)}명 발견\n")

    # 기존에 연락처가 없는 사람들만 필터링
    persons_without_contact = [p for p in persons if not p['phone'] and not p['email']]
    print(f"연락처 정보가 없는 사람: {len(persons_without_contact)}명\n")

    print("=" * 80)
    print("잠재적 매칭 분석")
    print("=" * 80)

    high_confidence_matches = []

    for person in persons_without_contact:
        matches = find_potential_matches(person, contacts)

        if matches:
            # 설정된 점수 이상만 표시
            top_matches = [m for m in matches if m['score'] >= args.min_score]

            if top_matches:
                high_confidence_matches.append({
                    'person': person,
                    'matches': top_matches[:3],  # 상위 3개만
                })

    # 결과 출력
    print(f"\n신뢰도 높은 매칭 후보: {len(high_confidence_matches)}건\n")

    for item in high_confidence_matches[:args.limit]:  # 설정된 개수만 출력
        person = item['person']
        print(f"\n📁 {person['file_path'].name}")
        print(f"   이름: {person['name']}, 소속: {person['org'] or '(없음)'}")

        for i, match in enumerate(item['matches'], 1):
            contact = match['contact']
            print(f"\n   {i}. 매칭 점수: {match['score']}점")
            print(f"      이름: {contact.get('structured_name') or contact.get('name', '(없음)')}")
            print(f"      소속: {contact.get('org', '(없음)')}")
            print(f"      전화: {contact.get('phone', '(없음)')}")
            print(f"      이메일: {contact.get('email', '(없음)')}")
            print(f"      이유: {', '.join(match['reasons'])}")

    if len(high_confidence_matches) > args.limit:
        print(f"\n... 외 {len(high_confidence_matches) - args.limit}건")

    print(f"\n\n총 {len(high_confidence_matches)}명에 대해 잠재적 매칭을 발견했습니다.")

if __name__ == '__main__':
    main()
