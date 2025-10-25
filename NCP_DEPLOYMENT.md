# 네이버 클라우드 플랫폼(NCP) 배포 가이드

## 1. NCP 계정 및 서비스 준비

### 1.1 NCP 계정 생성
- https://www.ncloud.com 에서 계정 생성
- 무료 크레딧 확인 (신규 가입 시 제공)

### 1.2 필요한 서비스 활성화
- **Cloud Functions**: 서버리스 함수 실행
- **Container Registry**: Docker 이미지 저장
- **Load Balancer**: 로드 밸런싱 (선택사항)

## 2. Docker 설정

### 2.1 Dockerfile 생성
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 포트 설정
EXPOSE 8000

# Django 마이그레이션 및 서버 실행
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
```

### 2.2 Docker 이미지 빌드 및 푸시
```bash
# Docker 이미지 빌드
docker build -t bus-data-collector .

# NCP Container Registry에 로그인
docker login your-registry.ncloud.com

# 이미지 태깅
docker tag bus-data-collector your-registry.ncloud.com/bus-data-collector:latest

# 이미지 푸시
docker push your-registry.ncloud.com/bus-data-collector:latest
```

## 3. Cloud Functions 배포

### 3.1 함수 설정
- **런타임**: Python 3.11
- **메모리**: 512MB (최소)
- **타임아웃**: 300초
- **트리거**: HTTP 요청

### 3.2 환경 변수 설정
```
GBIS_SERVICE_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
DEBUG=False
```

## 4. 스케줄러 설정

### 4.1 Cloud Functions 스케줄러
- **주기**: 2분마다 실행
- **함수**: 데이터 수집 함수 호출
- **설정**: Cron 표현식 사용

### 4.2 Cron 표현식 예시
```
*/2 * * * *  # 2분마다 실행
```

## 5. 데이터 저장소 설정

### 5.1 Object Storage 사용
- **버킷 생성**: bus-data-storage
- **폴더 구조**: /data/bus_data_234001730.json
- **접근 권한**: 퍼블릭 읽기

### 5.2 데이터 백업
- **자동 백업**: 일일 백업 설정
- **버전 관리**: 파일 버전 관리 활성화

## 6. 모니터링 및 로깅

### 6.1 Cloud Log Analytics
- 로그 수집 및 분석
- 오류 알림 설정
- 성능 모니터링

### 6.2 알림 설정
- 데이터 수집 실패 시 알림
- 서비스 장애 시 알림
- 이메일/SMS 알림 설정

## 7. 비용 최적화

### 7.1 무료 크레딧 활용
- 신규 가입 시 제공되는 크레딧 사용
- 월별 사용량 모니터링

### 7.2 리소스 최적화
- 최소 메모리 설정
- 불필요한 서비스 비활성화
- 자동 스케일링 설정

## 8. 보안 설정

### 8.1 접근 제어
- IP 화이트리스트 설정
- API 키 보안 관리
- HTTPS 강제 사용

### 8.2 데이터 보안
- 암호화 저장
- 접근 로그 관리
- 정기적인 보안 점검

## 9. 배포 후 확인사항

### 9.1 기능 테스트
- API 엔드포인트 테스트
- 데이터 수집 확인
- 웹 인터페이스 접근 확인

### 9.2 성능 모니터링
- 응답 시간 확인
- 메모리 사용량 모니터링
- 오류율 확인

## 10. 문제 해결

### 10.1 일반적인 문제
- 타임아웃 오류: 함수 타임아웃 증가
- 메모리 부족: 메모리 할당량 증가
- 네트워크 오류: 재시도 로직 추가

### 10.2 로그 확인
- Cloud Log Analytics에서 로그 확인
- 오류 메시지 분석
- 성능 지표 모니터링
