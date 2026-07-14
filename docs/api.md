# API 명세 초안

기준:

- 인증/인가 없음
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI: `/openapi.json`
- 기본 페이지 크기: 20
- 게시글 비밀번호는 해시 저장
- 이미지 저장은 로컬 디스크

## 공통 응답 원칙

- 성공 시 200/201
- 요청 오류 시 400
- 대상 없음 시 404
- 비밀번호 불일치 시 403
- 중복 좋아요/북마크 시 409

## 관광지

### GET `/api/tourism`

관광지 목록 조회

Query:

- `region` optional
- `q` optional

### GET `/api/tourism/{place_id}/location`

관광지 단건의 좌표 조회

Response:

- `id`
- `title`
- `mapx`
- `mapy`

## 게시글

### GET `/api/posts`

게시글 목록 조회

Query:

- `sort=latest|views|likes`
- `page` default 1
- `size` default 20

### GET `/api/posts/search?q=...`

게시글 검색

검색 대상:

- 제목
- 본문
- 닉네임

### POST `/api/posts`

게시글 생성

Form fields:

- `title`
- `content`
- `nickname`
- `password`
- `tags` comma-separated
- `images` up to 10 files

### GET `/api/posts/{post_id}`

게시글 상세 조회

동작:

- 조회수 1 증가
- 댓글/답글 트리 포함

### PUT `/api/posts/{post_id}`

게시글 수정

Body:

- `password`
- `title` optional
- `content` optional
- `nickname` optional
- `tags` optional

### DELETE `/api/posts/{post_id}`

게시글 삭제

Query:

- `password`

## 댓글/답글

### POST `/api/posts/{post_id}/comments`

댓글 또는 답글 생성

Body:

- `nickname`
- `content`
- `parent_id` optional

## 좋아요 / 북마크

### POST `/api/posts/{post_id}/like`

Body or query:

- `client_id`

### POST `/api/posts/{post_id}/bookmark`

Body or query:

- `client_id`

## 챗봇

### POST `/api/chat`

입력:

- `message`
- `client_id` optional

동작:

- 관광지 DB
- 축제 DB
- 음식점 DB
- 게시글 검색 결과

OpenAI API 실패 시:

- `오류가 발생했습니다`

