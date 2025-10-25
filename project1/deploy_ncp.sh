#!/bin/bash

# NCP 배포 스크립트

echo "🚌 NCP 버스 데이터 수집기 배포 시작..."

# 1. Docker 이미지 빌드
echo "📦 Docker 이미지 빌드 중..."
docker build -t bus-data-collector .

if [ $? -eq 0 ]; then
    echo "✅ Docker 이미지 빌드 완료"
else
    echo "❌ Docker 이미지 빌드 실패"
    exit 1
fi

# 2. NCP Container Registry 로그인
echo "🔐 NCP Container Registry 로그인 중..."
# docker login your-registry.ncloud.com

# 3. 이미지 태깅 및 푸시
echo "📤 이미지 푸시 중..."
# docker tag bus-data-collector your-registry.ncloud.com/bus-data-collector:latest
# docker push your-registry.ncloud.com/bus-data-collector:latest

# 4. 환경 변수 설정 확인
echo "🔧 환경 변수 설정 확인..."
echo "필요한 환경 변수:"
echo "- GBIS_SERVICE_KEY: GBIS API 키"
echo "- SECRET_KEY: Django 시크릿 키"
echo "- NCP_ACCESS_KEY: NCP 액세스 키"
echo "- NCP_SECRET_KEY: NCP 시크릿 키"
echo "- NCP_BUCKET_NAME: Object Storage 버킷명"

# 5. 배포 완료 안내
echo "🎉 배포 준비 완료!"
echo ""
echo "다음 단계:"
echo "1. NCP 콘솔에서 Cloud Functions 생성"
echo "2. Docker 이미지 배포"
echo "3. 환경 변수 설정"
echo "4. 스케줄러 설정 (2분마다 실행)"
echo "5. Object Storage 버킷 생성"
echo ""
echo "자세한 내용은 NCP_DEPLOYMENT.md 파일을 참조하세요."
