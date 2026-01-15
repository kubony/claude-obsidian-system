#!/usr/bin/env python3
"""
iCloud/Google 연락처에서 인물사전 파일 연락처 정보 업데이트

VCF 또는 CSV 파일을 파싱하여 인물사전의 contact 필드를 업데이트합니다.
"""

import re
import sys
import csv
from pathlib import Path
from typing import Dict, List, Optional
import unicodedata

def normalize_str(s: str) -> str:
    """macOS NFD → NFC 정규화"""
    return unicodedata.normalize('NFC', s)

try:
    import yaml
except ImportError:
    print("Error: PyYAML required. Install with: pip install pyyaml")
    sys.exit(1)


class VCardParser:
    """VCF 파일 파서"""

    @staticmethod
    def parse_vcf_file(vcf_path: Path) -> List[Dict]:
        """VCF 파일에서 연락처 추출"""
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
                    VCardParser._parse_vcard_line(line, current_contact)

        return contacts

    @staticmethod
    def _parse_vcard_line(line: str, contact: Dict):
        """VCard 라인 파싱"""
        # FN (Full Name)
        if line.startswith('FN:'):
            contact['name'] = line.split(':', 1)[1].strip()

        # N (Structured Name: 성;이름)
        elif line.startswith('N:'):
            parts = line.split(':', 1)[1].split(';')
            if len(parts) >= 2:
                surname = parts[0].strip()
                given = parts[1].strip()
                if surname and given:
                    # given이 이미 surname으로 시작하는 경우 중복 제거
                    # 예: "윤;윤건호" → "윤건호" (not "윤윤건호")
                    if given.startswith(surname):
                        contact['structured_name'] = given
                    else:
                        contact['structured_name'] = f"{surname}{given}"
                elif given:
                    contact['structured_name'] = given

        # TEL (Phone)
        elif line.startswith('TEL'):
            phone = line.split(':', 1)[1].strip()
            # 국제 형식 처리 (+82 → 0)
            phone = re.sub(r'^\+82[\s-]?', '0', phone)
            # 모든 공백, 하이픈, 괄호 제거
            phone = re.sub(r'[\s\-\(\)]', '', phone)
            # 숫자만 추출
            phone = re.sub(r'[^\d]', '', phone)
            # 11자리 숫자인 경우에만 포맷팅
            if len(phone) == 11 and phone.startswith('010'):
                phone = f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                if 'phone' not in contact:
                    contact['phone'] = phone
            elif len(phone) == 10 and phone.startswith('0'):
                phone = f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                if 'phone' not in contact:
                    contact['phone'] = phone

        # EMAIL
        elif line.startswith('EMAIL'):
            email = line.split(':', 1)[1].strip()
            if 'email' not in contact:
                contact['email'] = email

        # ORG (Organization)
        elif line.startswith('ORG:'):
            org = line.split(':', 1)[1].split(';')[0].strip()
            if org:
                contact['org'] = org

        # Social profiles
        elif 'linkedin' in line.lower():
            contact['linkedin'] = line.split(':', 1)[1].strip()
        elif 'facebook' in line.lower() and 'linkedin' not in contact:
            # LinkedIn이 없을 때만 Facebook을 저장
            pass
        elif 'X-SOCIALPROFILE' in line and 'type=kakao' in line.lower():
            contact['kakao'] = line.split(':', 1)[1].strip()


class GoogleCSVParser:
    """Google Contacts CSV 파서"""

    @staticmethod
    def parse_csv_file(csv_path: Path) -> List[Dict]:
        """Google Contacts CSV에서 연락처 추출"""
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
    except yaml.YAMLError as e:
        print(f"YAML 파싱 오류: {e}")
        return {}, content


def extract_name_from_filename(filename: str) -> str:
    """파일명에서 이름 추출 (이름_소속.md → 이름)"""
    name = filename.replace('.md', '')
    if '_' in name:
        return name.split('_')[0]
    return name


def extract_org_from_filename(filename: str) -> str:
    """파일명에서 소속 추출 (이름_소속.md → 소속)"""
    name = filename.replace('.md', '')
    if '_' in name:
        return name.split('_', 1)[1]  # 첫 번째 _ 이후 전체
    return ''


def normalize_org_name(org: str) -> str:
    """소속명 정규화 (비교용)"""
    if not org:
        return ''
    org = normalize_str(org).strip().lower()
    # 일반적인 변형 통일
    org = org.replace('(주)', '').replace('주식회사', '').replace(' ', '')
    return org


# 이메일 도메인 → 소속 매핑 (회사 도메인만, 개인 이메일 서비스 제외)
EMAIL_DOMAIN_TO_ORG = {
    # 현대/기아 그룹
    'kefico.co.kr': '현대케피코',
    'hyundai-kefico.com': '현대케피코',
    'hyundai.com': '현대자동차',
    'hmg.com': '현대자동차그룹',
    'kia.com': '기아',
    # LG 그룹
    'lgchem.com': 'LG화학',
    'lges.com': 'LG에너지솔루션',
    # 삼성 그룹
    'samsung.com': '삼성',
    'samsungsdi.com': '삼성SDI',
    # 스타트업/기타
    'nuvi-labs.com': '누비랩',
    'nuvilab.com': '누비랩',
    'antler.co': '앤틀러코리아',
    'maum.ai': '마음AI',
    'angelswing.io': '엔젤스윙',
    'fescaro.com': '페스카로',
    'signetev.com': '시그넷EV',
    # 대학/기관
    'catholic.ac.kr': '가톨릭대학교',
}

# 개인 이메일 서비스 (소속 추론 제외)
PERSONAL_EMAIL_DOMAINS = {
    'gmail.com', 'naver.com', 'hanmail.net', 'daum.net',
    'kakao.com', 'nate.com', 'hotmail.com', 'outlook.com',
    'yahoo.com', 'icloud.com', 'me.com', 'live.com',
}


def infer_org_from_email(email: str) -> str:
    """이메일 도메인에서 소속 추론 (개인 이메일 서비스 제외)"""
    if not email or '@' not in email:
        return ''

    domain = email.split('@')[1].lower()

    # 개인 이메일 서비스는 소속 추론 불가
    if domain in PERSONAL_EMAIL_DOMAINS:
        return ''

    # 직접 매핑 확인
    if domain in EMAIL_DOMAIN_TO_ORG:
        return EMAIL_DOMAIN_TO_ORG[domain]

    # 서브도메인 처리 (예: mail.company.com → company.com)
    parts = domain.split('.')
    if len(parts) > 2:
        parent_domain = '.'.join(parts[-2:])
        if parent_domain in PERSONAL_EMAIL_DOMAINS:
            return ''
        if parent_domain in EMAIL_DOMAIN_TO_ORG:
            return EMAIL_DOMAIN_TO_ORG[parent_domain]

    return ''


def orgs_match(csv_org: str, file_org: str) -> bool:
    """CSV 소속과 파일 소속이 일치하는지 확인"""
    if not csv_org or not file_org:
        return False  # 소속 정보가 없으면 일치로 판단하지 않음

    csv_normalized = normalize_org_name(csv_org)
    file_normalized = normalize_org_name(file_org)

    if not csv_normalized or not file_normalized:
        return False

    # 정확히 일치하거나 포함 관계
    return (csv_normalized == file_normalized or
            csv_normalized in file_normalized or
            file_normalized in csv_normalized)


def match_contact_to_file(contact: Dict, person_files: List[Path]) -> Optional[Path]:
    """연락처와 인물사전 파일 매칭

    매칭 전략:
    1. 이름으로 매칭되는 파일들을 모두 찾음
    2. 1개만 있으면 → 그대로 매칭
    3. 2개 이상 있으면 (동명이인) → 소속으로 구분
       - 소속 일치 파일 1개 → 매칭
       - 구분 불가 → 스킵 + 경고
    """
    # 이름 정규화
    contact_name = contact.get('structured_name') or contact.get('name', '')
    contact_name = normalize_str(contact_name).strip()

    # 불필요한 텍스트 제거 (예: "연구원", "대리", 날짜 등)
    contact_name = re.sub(r'\d{8}', '', contact_name)  # 날짜 제거
    contact_name = re.sub(r'(연구원|대리|선임|책임|과장|부장|이사|사원|팀장|매니저|대표|본부장|전무|상무|부사장|사장|회장|실장|차장|대표님)\s*', '', contact_name)
    contact_name = contact_name.strip()

    # 공백 또는 점(.)으로 분리된 경우 첫 번째 단어만 사용 (이름만 추출)
    # 예: "권현정 위자드랩" → "권현정", "이상기.큐엠아이티" → "이상기"
    if ' ' in contact_name:
        contact_name = contact_name.split()[0]
    elif '.' in contact_name:
        contact_name = contact_name.split('.')[0]

    # 빈 이름 또는 너무 짧은 이름은 스킵 (오매칭 방지)
    if not contact_name or len(contact_name) < 2:
        return None

    # 1단계: 이름으로 매칭되는 모든 파일 찾기
    matched_files = []
    for file_path in person_files:
        file_name = extract_name_from_filename(file_path.name)
        file_name = normalize_str(file_name).strip()

        # 최소 길이 체크 후 매칭 (오매칭 방지)
        if len(file_name) >= 2:
            # 정확히 일치하거나, 연락처 이름이 파일명에 포함되는 경우
            if contact_name == file_name or contact_name in file_name:
                matched_files.append(file_path)

    # 매칭된 파일이 없으면 None
    if not matched_files:
        return None

    # 2단계: 1개만 매칭된 경우
    if len(matched_files) == 1:
        # CSV 소속 정보 (없으면 이메일 도메인에서 추론)
        csv_org = contact.get('org', '')
        if not csv_org:
            csv_org = infer_org_from_email(contact.get('email', ''))
            if csv_org:
                contact['org_inferred'] = True  # 추론된 소속임을 표시

        if csv_org:
            file_org = extract_org_from_filename(matched_files[0].name)
            if file_org and not orgs_match(csv_org, file_org):
                inferred_tag = " (이메일 추론)" if contact.get('org_inferred') else ""
                print(f"  [SKIP] 소속 불일치: {contact_name} ({csv_org}{inferred_tag}) → {matched_files[0].name} ({file_org})")
                return None
        return matched_files[0]

    # 3단계: 동명이인 - 소속으로 구분 시도
    # CSV 소속 정보 (없으면 이메일 도메인에서 추론)
    csv_org = contact.get('org', '')
    if not csv_org:
        csv_org = infer_org_from_email(contact.get('email', ''))
        if csv_org:
            contact['org_inferred'] = True

    if not csv_org:
        # CSV에 소속 정보가 없으면 구분 불가 → 스킵
        names = [f.name for f in matched_files]
        print(f"  [SKIP] 동명이인 발견, 소속 정보 없음: {contact_name} → {names}")
        return None

    # 소속이 일치하는 파일 찾기
    org_matched_files = []
    for file_path in matched_files:
        file_org = extract_org_from_filename(file_path.name)
        if orgs_match(csv_org, file_org):
            org_matched_files.append(file_path)

    if len(org_matched_files) == 1:
        # 소속으로 구분 성공
        return org_matched_files[0]
    elif len(org_matched_files) == 0:
        # 소속 일치하는 파일 없음 → 스킵
        names = [f.name for f in matched_files]
        print(f"  [SKIP] 동명이인 발견, 소속 불일치: {contact_name} ({csv_org}) → {names}")
        return None
    else:
        # 여전히 여러 개 → 스킵
        names = [f.name for f in org_matched_files]
        print(f"  [SKIP] 동명이인 발견, 구분 불가: {contact_name} ({csv_org}) → {names}")
        return None


def update_file_contact(file_path: Path, contact: Dict, dry_run=False) -> dict:
    """파일의 contact 필드 업데이트"""
    content = file_path.read_text(encoding='utf-8')
    content = normalize_str(content)

    metadata, body = parse_yaml_frontmatter(content)

    # 기존 contact 필드 가져오기 또는 초기화
    if 'contact' not in metadata:
        metadata['contact'] = {}

    contact_field = metadata['contact']
    if not isinstance(contact_field, dict):
        contact_field = {}

    # 빈 필드 초기화
    for field in ['phone', 'email', 'linkedin', 'slack', 'discord', 'kakao', 'instagram', 'twitter', 'github', 'website']:
        if field not in contact_field:
            contact_field[field] = None

    result = {
        'file': file_path.name,
        'updated_fields': [],
        'updated': False,
    }

    # 전화번호 업데이트
    if contact.get('phone') and not contact_field.get('phone'):
        contact_field['phone'] = contact['phone']
        result['updated_fields'].append('phone')
        result['updated'] = True

    # 이메일 업데이트
    if contact.get('email') and not contact_field.get('email'):
        contact_field['email'] = contact['email']
        result['updated_fields'].append('email')
        result['updated'] = True

    # LinkedIn 업데이트
    if contact.get('linkedin') and not contact_field.get('linkedin'):
        contact_field['linkedin'] = contact['linkedin']
        result['updated_fields'].append('linkedin')
        result['updated'] = True

    # Kakao 업데이트
    if contact.get('kakao') and not contact_field.get('kakao'):
        contact_field['kakao'] = contact['kakao']
        result['updated_fields'].append('kakao')
        result['updated'] = True

    metadata['contact'] = contact_field

    if result['updated'] and not dry_run:
        # YAML frontmatter 재구성
        yaml_str = yaml.dump(metadata, allow_unicode=True, sort_keys=False, default_flow_style=False)
        new_content = f"---\n{yaml_str}---\n\n{body}"
        file_path.write_text(new_content, encoding='utf-8')

    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description='iCloud/Google 연락처로 인물사전 업데이트')
    parser.add_argument('contact_file', help='VCF 또는 CSV 파일 경로')
    parser.add_argument('person_dir', help='인물사전 디렉토리 경로')
    parser.add_argument('--dry-run', action='store_true', help='실제 파일 수정 없이 미리보기만')

    args = parser.parse_args()

    contact_file = Path(args.contact_file)
    person_dir = Path(args.person_dir)

    if not contact_file.exists():
        print(f"Error: 연락처 파일을 찾을 수 없습니다: {contact_file}")
        sys.exit(1)

    if not person_dir.exists():
        print(f"Error: 인물사전 디렉토리를 찾을 수 없습니다: {person_dir}")
        sys.exit(1)

    # 파일 형식 감지 및 파싱
    file_ext = contact_file.suffix.lower()

    if file_ext == '.vcf':
        print(f"{'[DRY RUN] ' if args.dry_run else ''}VCF 파일 파싱 중...\n")
        contacts = VCardParser.parse_vcf_file(contact_file)
    elif file_ext == '.csv':
        print(f"{'[DRY RUN] ' if args.dry_run else ''}Google CSV 파일 파싱 중...\n")
        contacts = GoogleCSVParser.parse_csv_file(contact_file)
    else:
        print(f"Error: 지원하지 않는 파일 형식입니다. VCF 또는 CSV 파일을 사용하세요.")
        sys.exit(1)

    print(f"총 {len(contacts)}개 연락처 발견\n")

    # 인물사전 파일 목록
    person_files = sorted(person_dir.glob('*.md'))
    print(f"인물사전 파일 {len(person_files)}개\n")

    # 매칭 및 업데이트
    stats = {
        'total_contacts': len(contacts),
        'matched': 0,
        'updated': 0,
        'skipped': 0,
    }

    results = []

    for contact in contacts:
        matched_file = match_contact_to_file(contact, person_files)

        if matched_file:
            stats['matched'] += 1
            result = update_file_contact(matched_file, contact, dry_run=args.dry_run)

            if result['updated']:
                stats['updated'] += 1
                results.append(result)
            else:
                stats['skipped'] += 1

    # 결과 출력
    if results:
        print("\n## 업데이트된 파일:\n")
        for r in results[:30]:
            fields = ', '.join(r['updated_fields'])
            print(f"  {r['file']}: {fields}")

        if len(results) > 30:
            print(f"  ... 외 {len(results) - 30}개")

    # 통계 출력
    print(f"\n## 통계:")
    print(f"  - 총 연락처: {stats['total_contacts']}개")
    print(f"  - 매칭됨: {stats['matched']}개")
    print(f"  - 업데이트됨: {stats['updated']}개")
    print(f"  - 스킵 (이미 있음): {stats['skipped']}개")
    print(f"  - 매칭 실패: {stats['total_contacts'] - stats['matched']}개")

    if args.dry_run:
        print("\n[DRY RUN] 실제 파일은 수정되지 않았습니다.")
        print("실제 업데이트하려면 --dry-run 옵션을 제거하세요.")


if __name__ == '__main__':
    main()
