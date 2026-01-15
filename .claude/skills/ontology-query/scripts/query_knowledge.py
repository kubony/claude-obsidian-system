#!/usr/bin/env python3
"""
SPARQL 질의 스크립트

TTL 파일을 로드하고 SPARQL 질의를 수행합니다.

Usage:
    python query_knowledge.py <ttl_file> --query <sparql_query>
    python query_knowledge.py <ttl_file> --preset <preset_name> [--param <value>]
    python query_knowledge.py <ttl_file> --interactive

Example:
    python query_knowledge.py knowledge.ttl --preset person_meetings --param "신동순"
    python query_knowledge.py knowledge.ttl --query "SELECT ?name WHERE { ?p a :Person ; :name ?name }"
"""

import argparse
import sys
from pathlib import Path

try:
    from rdflib import Graph, Namespace
except ImportError:
    print("Error: rdflib required. Install with: pip install rdflib")
    sys.exit(1)


ONT = Namespace("http://obsidian.local/ontology#")
DATA = Namespace("http://obsidian.local/data#")


# 프리셋 쿼리 정의
PRESET_QUERIES = {
    "all_persons": {
        "description": "모든 인물 목록",
        "query": """
            SELECT ?name ?affiliation ?summary
            WHERE {
                ?person a :Person ;
                        :name ?name .
                OPTIONAL { ?person :affiliatedWith ?org . ?org :name ?affiliation }
                OPTIONAL { ?person :summary ?summary }
            }
            ORDER BY ?name
        """
    },
    "person_meetings": {
        "description": "특정 인물과의 모든 미팅 (param: 인물명)",
        "query": """
            SELECT ?date ?summary
            WHERE {
                ?person a :Person ;
                        :name ?name .
                FILTER(CONTAINS(LCASE(STR(?name)), LCASE("{param}")))
                ?meeting a :Meeting ;
                         :participant ?person ;
                         :date ?date .
                OPTIONAL { ?meeting :summary ?summary }
            }
            ORDER BY DESC(?date)
        """
    },
    "person_topics": {
        "description": "특정 인물과 논의한 주제들 (param: 인물명)",
        "query": """
            SELECT DISTINCT ?topic_name ?date
            WHERE {
                ?person a :Person ;
                        :name ?name .
                FILTER(CONTAINS(LCASE(STR(?name)), LCASE("{param}")))
                ?meeting :participant ?person ;
                         :date ?date ;
                         :hasTopic ?topic .
                ?topic :name ?topic_name .
            }
            ORDER BY DESC(?date)
        """
    },
    "meetings_by_date": {
        "description": "특정 기간 미팅 목록 (param: YYYY-MM 형식)",
        "query": """
            SELECT ?person_name ?date ?summary
            WHERE {
                ?meeting a :Meeting ;
                         :participant ?person ;
                         :date ?date .
                ?person :name ?person_name .
                FILTER(STRSTARTS(STR(?date), "{param}"))
                OPTIONAL { ?meeting :summary ?summary }
            }
            ORDER BY DESC(?date)
        """
    },
    "org_members": {
        "description": "특정 조직 소속 인물들 (param: 조직명)",
        "query": """
            SELECT ?name ?summary
            WHERE {
                ?org a :Organization ;
                     :name ?org_name .
                FILTER(CONTAINS(LCASE(STR(?org_name)), LCASE("{param}")))
                ?person :affiliatedWith ?org ;
                        :name ?name .
                OPTIONAL { ?person :summary ?summary }
            }
            ORDER BY ?name
        """
    },
    "person_network": {
        "description": "특정 인물이 아는 사람들 (param: 인물명)",
        "query": """
            SELECT ?related_name
            WHERE {
                ?person a :Person ;
                        :name ?name .
                FILTER(CONTAINS(LCASE(STR(?name)), LCASE("{param}")))
                ?person :knows ?related .
                ?related :name ?related_name .
            }
        """
    },
    "recent_meetings": {
        "description": "최근 미팅 10개",
        "query": """
            SELECT ?person_name ?date ?summary
            WHERE {
                ?meeting a :Meeting ;
                         :participant ?person ;
                         :date ?date .
                ?person :name ?person_name .
                OPTIONAL { ?meeting :summary ?summary }
            }
            ORDER BY DESC(?date)
            LIMIT 10
        """
    },
    "stats": {
        "description": "전체 통계",
        "query": """
            SELECT
                (COUNT(DISTINCT ?person) AS ?persons)
                (COUNT(DISTINCT ?project) AS ?projects)
                (COUNT(DISTINCT ?meeting) AS ?meetings)
                (COUNT(DISTINCT ?org) AS ?organizations)
                (COUNT(DISTINCT ?topic) AS ?topics)
            WHERE {
                { ?person a :Person }
                UNION { ?project a :Project }
                UNION { ?meeting a :Meeting }
                UNION { ?org a :Organization }
                UNION { ?topic a :Topic }
            }
        """
    },
    "search_keyword": {
        "description": "키워드로 미팅 검색 (param: 키워드)",
        "query": """
            SELECT ?person_name ?date ?summary
            WHERE {
                ?meeting a :Meeting ;
                         :participant ?person ;
                         :date ?date ;
                         :summary ?summary .
                ?person :name ?person_name .
                FILTER(CONTAINS(LCASE(STR(?summary)), LCASE("{param}")))
            }
            ORDER BY DESC(?date)
        """
    },
    # =========================================================================
    # 프로젝트 관련 쿼리
    # =========================================================================
    "all_projects": {
        "description": "모든 프로젝트 목록",
        "query": """
            SELECT ?name ?date ?summary
            WHERE {
                ?project a :Project ;
                         :name ?name .
                OPTIONAL { ?project :date ?date }
                OPTIONAL { ?project :summary ?summary }
            }
            ORDER BY DESC(?date)
        """
    },
    "active_projects": {
        "description": "활성 프로젝트 (archived 태그 없는)",
        "query": """
            SELECT ?name ?date ?summary
            WHERE {
                ?project a :Project ;
                         :name ?name .
                OPTIONAL { ?project :date ?date }
                OPTIONAL { ?project :summary ?summary }
                FILTER NOT EXISTS { ?project :tag "archived"@en }
            }
            ORDER BY DESC(?date)
        """
    },
    "archived_projects": {
        "description": "아카이브된 프로젝트",
        "query": """
            SELECT ?name ?date ?summary
            WHERE {
                ?project a :Project ;
                         :name ?name ;
                         :tag "archived"@en .
                OPTIONAL { ?project :date ?date }
                OPTIONAL { ?project :summary ?summary }
            }
            ORDER BY DESC(?date)
        """
    },
    "project_details": {
        "description": "특정 프로젝트 상세 (param: 프로젝트명)",
        "query": """
            SELECT ?name ?date ?summary ?tag
            WHERE {
                ?project a :Project ;
                         :name ?name .
                FILTER(CONTAINS(LCASE(STR(?name)), LCASE("{param}")))
                OPTIONAL { ?project :date ?date }
                OPTIONAL { ?project :summary ?summary }
                OPTIONAL { ?project :tag ?tag }
            }
        """
    },
    "project_meetings": {
        "description": "특정 프로젝트의 미팅/로그 (param: 프로젝트명)",
        "query": """
            SELECT ?date ?summary
            WHERE {
                ?project a :Project ;
                         :name ?pname .
                FILTER(CONTAINS(LCASE(STR(?pname)), LCASE("{param}")))
                ?meeting :relatedTo ?project ;
                         :date ?date .
                OPTIONAL { ?meeting :summary ?summary }
            }
            ORDER BY DESC(?date)
        """
    },
    "project_participants": {
        "description": "특정 프로젝트 참여 인물 (param: 프로젝트명)",
        "query": """
            SELECT DISTINCT ?person_name
            WHERE {
                ?project a :Project ;
                         :name ?pname .
                FILTER(CONTAINS(LCASE(STR(?pname)), LCASE("{param}")))
                ?person :involvedIn ?project ;
                        :name ?person_name .
            }
            ORDER BY ?person_name
        """
    },
    "person_projects": {
        "description": "특정 인물이 참여한 프로젝트 (param: 인물명)",
        "query": """
            SELECT ?project_name ?date
            WHERE {
                ?person a :Person ;
                        :name ?name .
                FILTER(CONTAINS(LCASE(STR(?name)), LCASE("{param}")))
                ?person :involvedIn ?project .
                ?project :name ?project_name .
                OPTIONAL { ?project :date ?date }
            }
            ORDER BY DESC(?date)
        """
    },
    "search_projects": {
        "description": "프로젝트 키워드 검색 (param: 키워드)",
        "query": """
            SELECT ?name ?date ?summary
            WHERE {
                ?project a :Project ;
                         :name ?name .
                OPTIONAL { ?project :date ?date }
                OPTIONAL { ?project :summary ?summary }
                FILTER(
                    CONTAINS(LCASE(STR(?name)), LCASE("{param}")) ||
                    CONTAINS(LCASE(STR(?summary)), LCASE("{param}"))
                )
            }
            ORDER BY DESC(?date)
        """
    }
}


def load_graph(ttl_path: Path) -> Graph:
    """TTL 파일 로드"""
    g = Graph()
    g.bind('', ONT)
    g.bind('data', DATA)
    g.parse(str(ttl_path), format='turtle')
    return g


def execute_query(graph: Graph, query: str):
    """SPARQL 쿼리 실행 - Result 객체 반환"""
    # 프리픽스 추가
    full_query = f"""
        PREFIX : <http://obsidian.local/ontology#>
        PREFIX data: <http://obsidian.local/data#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        {query}
    """

    return graph.query(full_query)


def format_results(results, variables: list = None) -> str:
    """결과 포맷팅"""
    # Result 객체를 리스트로 변환
    rows = list(results)
    if not rows:
        return "결과 없음"

    # variables가 없으면 Result 객체에서 가져오기
    if variables is None:
        variables = getattr(results, 'vars', [])

    output = []

    # 헤더
    header = " | ".join(str(v) for v in variables)
    output.append(header)
    output.append("-" * len(header))

    # 데이터
    for row in rows:
        values = []
        for val in row:
            if val is None:
                values.append("-")
            else:
                val_str = str(val)
                # 긴 텍스트 줄임
                if len(val_str) > 80:
                    val_str = val_str[:77] + "..."
                values.append(val_str)
        output.append(" | ".join(values))

    return "\n".join(output)


def interactive_mode(graph: Graph):
    """대화형 모드"""
    print("\n=== 온톨로지 질의 대화형 모드 ===")
    print("사용 가능한 프리셋:")
    for name, preset in PRESET_QUERIES.items():
        print(f"  - {name}: {preset['description']}")
    print("\n종료: exit 또는 quit")
    print("커스텀 쿼리: query <SPARQL>")
    print("프리셋 사용: <preset_name> [param]\n")

    while True:
        try:
            user_input = input("질의> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not user_input:
            continue

        if user_input.lower() in ('exit', 'quit'):
            print("종료합니다.")
            break

        # 커스텀 쿼리
        if user_input.lower().startswith('query '):
            query = user_input[6:]
            try:
                results = execute_query(graph, query)
                if results:
                    print(format_results(results, results.vars))
                else:
                    print("결과 없음")
            except Exception as e:
                print(f"쿼리 오류: {e}")
            continue

        # 프리셋 쿼리
        parts = user_input.split(maxsplit=1)
        preset_name = parts[0]
        param = parts[1] if len(parts) > 1 else ""

        if preset_name not in PRESET_QUERIES:
            print(f"알 수 없는 프리셋: {preset_name}")
            continue

        preset = PRESET_QUERIES[preset_name]
        query = preset['query'].replace("{param}", param)

        try:
            results = execute_query(graph, query)
            if results:
                print(format_results(results, results.vars))
            else:
                print("결과 없음")
        except Exception as e:
            print(f"쿼리 오류: {e}")

        print()


def main():
    parser = argparse.ArgumentParser(
        description='온톨로지 SPARQL 질의'
    )
    parser.add_argument('ttl_file', help='TTL 파일 경로')
    parser.add_argument('--query', '-q', help='SPARQL 쿼리')
    parser.add_argument('--preset', '-p', choices=list(PRESET_QUERIES.keys()),
                        help='프리셋 쿼리')
    parser.add_argument('--param', default='', help='프리셋 쿼리 파라미터')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='대화형 모드')
    parser.add_argument('--list-presets', action='store_true',
                        help='프리셋 목록 출력')

    args = parser.parse_args()

    # 프리셋 목록
    if args.list_presets:
        print("사용 가능한 프리셋 쿼리:")
        for name, preset in PRESET_QUERIES.items():
            print(f"\n  {name}")
            print(f"    설명: {preset['description']}")
        sys.exit(0)

    ttl_path = Path(args.ttl_file)
    if not ttl_path.exists():
        print(f"Error: TTL 파일을 찾을 수 없습니다: {ttl_path}")
        sys.exit(1)

    print(f"TTL 로드 중: {ttl_path}")
    graph = load_graph(ttl_path)
    print(f"트리플 수: {len(graph)}")

    # 대화형 모드
    if args.interactive:
        interactive_mode(graph)
        return

    # 쿼리 실행
    if args.query:
        query = args.query
    elif args.preset:
        preset = PRESET_QUERIES[args.preset]
        query = preset['query'].replace("{param}", args.param)
        print(f"\n프리셋: {args.preset} - {preset['description']}")
    else:
        print("Error: --query, --preset, 또는 --interactive 옵션이 필요합니다")
        sys.exit(1)

    try:
        results = execute_query(graph, query)
        rows = list(results)
        print(f"\n결과 ({len(rows)}건):")
        print(format_results(rows, results.vars))
    except Exception as e:
        print(f"쿼리 오류: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
