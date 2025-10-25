# 경기도 버스 좌석수 조회 시스템

이 프로젝트는 경기도 버스 정보 시스템(GBIS) API를 활용하여 버스의 잔여 좌석수를 조회하는 Django 웹 애플리케이션입니다.

## 기능

- 버스 노선별 실시간 좌석수 조회
- 차량별 상세 정보 제공 (차량번호, 혼잡도, 정류소 정보 등)
- RESTful API 형태로 데이터 제공

## 설치 및 실행

### 1. 가상환경 설정 (권장)
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 마이그레이션
```bash
python manage.py migrate
```

### 4. 서버 실행
```bash
python manage.py runserver
```

## API 사용법

### 1. 버스 좌석수 조회
```
GET /api/bus-seat/?routeId=233000031
```

**파라미터:**
- `routeId` (필수): 노선 ID

**응답 예시:**
```json
{
  "success": true,
  "routeId": "233000031",
  "queryTime": "2024-01-01 12:00:00",
  "busCount": 2,
  "busList": [
    {
      "plateNo": "경기12가3456",
      "routeId": 233000031,
      "remainSeatCnt": 15,
      "seatInfo": "잔여 좌석: 15개",
      "crowded": 2,
      "crowdedInfo": "보통",
      "routeTypeCd": 13,
      "stationId": 123456,
      "stationSeq": 5,
      "stateCd": 1
    }
  ]
}
```

### 2. API 정보 조회
```
GET /api/route-info/
```

## 중요 사항

⚠️ **서비스키 설정 필요**: 실제 사용을 위해서는 공공데이터포털(https://data.go.kr)에서 GBIS API 서비스키를 발급받아 `bus_info/views.py` 파일의 `service_key` 변수를 실제 키로 교체해야 합니다.

## API 응답 필드 설명

- `remainSeatCnt`: 잔여 좌석수 (-1: 정보없음, 0~: 빈자리 수)
- `crowded`: 차내혼잡도 (1:여유, 2:보통, 3:혼잡, 4:매우혼잡)
- `routeTypeCd`: 노선유형코드
- `stateCd`: 상태코드 (0:교차로통과, 1:정류소 도착, 2:정류소 출발)

## 참고 자료

- [GBIS 공유서비스](https://www.gbis.go.kr/gbis2014/publicService.action?cmd=mBusLocation)
- [공공데이터포털](https://data.go.kr)
