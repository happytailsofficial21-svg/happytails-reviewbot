# 해피테일즈 리뷰봇 (HappyTails ReviewBot)

네이버 스마트스토어 리뷰 관리 자동화 시스템

## 📁 구조

```
happytails-reviewbot/
├── docs/                    # 지침 & DB 문서
│   ├── 답변원칙_v6.md         # 답변 작성 핵심 원칙
│   ├── 인사말DB_v2.md         # 인사말 + 마무리 인사 DB
│   ├── 제품자랑DB_v1_3.md     # 킬러카피 DB (87K 리뷰 기반)
│   ├── 패턴학습_v2.md         # 3,704개 답글 분석 결과
│   ├── 상품DB_v1_1.md         # 전체 52개 상품 목록
│   ├── 리뷰DB_v1.md           # 리뷰 데이터 축적용
│   ├── 답변템플릿_v1.md       # 답변 뼈대 참고용
│   ├── 리뷰답글_워크플로우_v1.md  # 주간 워크플로우
│   ├── 히스토리_리뷰_v1_9.md   # 프로젝트 진행 히스토리
│   └── 주간태스크_v1_5.md      # 주간 체크리스트
├── crawlers/                # 크롤러 스크립트
│   ├── smartstore_product_crawler_v1_6.py
│   └── smartstore_review_crawler_v4_8.py
├── data/                    # 데이터 파일
│   └── reviews_replied_pattern.csv
├── prompts/                 # 시스템 프롬프트
│   └── system_prompt_v5.md
└── README.md
```

## 🏷️ 브랜드

| 브랜드 | 상품수 | 대상 |
|:------:|:------:|:----:|
| 해피테일즈 | 11 | 임산부 |
| 슬립빈 | 3 | 아기 |
| 코코테일즈 | 2 | 아기 |
| 에르니 | 6 | 공용 |
| 틴더버드 | 7 | 아기 |
| 쿨리베어 | 4 | 아기 |
| 기타 | 19 | - |

## 📊 데이터 현황

- 전체 리뷰: 87,003개
- 답글 분석: 3,704개
- 상품: 52개

## ⚙️ 사용법

### Claude 프로젝트에서 사용
시스템 프롬프트에 `prompts/system_prompt_v5.md` 내용을 붙여넣기.
각 지침 파일은 GitHub raw URL로 참조.

### 크롤러 실행
```bash
# 상품 크롤링
python crawlers/smartstore_product_crawler_v1_6.py

# 리뷰 크롤링
python crawlers/smartstore_review_crawler_v4_8.py
```

## 📋 버전 현황

| 파일 | 버전 | 최종 수정 |
|------|:----:|:---------:|
| 답변원칙 | v6 | 2026.01.26 |
| 인사말DB | v2 | 2026.01.26 |
| 제품자랑DB | v1.3 | 2026.01.12 |
| 패턴학습 | v2 | 2026.01.26 |
| 상품DB | v1.1 | 2026.01.07 |
| 상품 크롤러 | v1_6 | 2026.01.07 |
| 리뷰 크롤러 | v4_8 | 2026.01.07 |

---

*해피테일즈 (HappyTails) - 엄마가 만든 육아 브랜드*
