# GBIS API 설정
# 실제 사용시에는 공공데이터포털(https://data.go.kr)에서 발급받은 서비스키를 사용하세요

# 공공데이터포털에서 발급받은 GBIS API 서비스키
GBIS_SERVICE_KEY = "KkkVy4H1CGa8fSuj2QR5%2BSHvd1oyW2RO%2FmtyS2Sr6ExzX34N5NoaduPT%2BpIuyWLRcQcIkJGT3OI%2Bu3Mv7mH9qA%3D%3D"

# API 기본 설정
GBIS_API_BASE_URL = "https://apis.data.go.kr/6410000/buslocationservice/v2"
GBIS_API_ENDPOINT = f"{GBIS_API_BASE_URL}/getBusLocationListv2"

# API 요청 타임아웃 (초)
API_TIMEOUT = 10

# 응답 포맷
RESPONSE_FORMAT = "json"

# 좌석수 제공 노선 유형 코드
SEAT_INFO_ROUTE_TYPES = [
    11,  # 직행좌석형시내버스
    12,  # 좌석형시내버스
    14,  # 광역급행형시내버스
    16,  # 경기순환버스
    17,  # 준공영제직행좌석시내버스
    21,  # 직행좌석형농어촌버스
    22,  # 좌석형농어촌버스
]

# 혼잡도 제공 노선 유형 코드
CROWDED_INFO_ROUTE_TYPES = [
    13,  # 일반형시내버스
    15,  # 따복형시내버스
    23,  # 일반형농어촌버스
]
