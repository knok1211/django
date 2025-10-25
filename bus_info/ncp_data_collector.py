import json
import os
import threading
import time
from datetime import datetime
from django.conf import settings
import requests
import urllib.parse
import boto3
from botocore.exceptions import ClientError


class NCPObjectStorage:
    """
    NCP Object Storage 클라이언트
    """
    
    def __init__(self):
        self.access_key = os.environ.get('NCP_ACCESS_KEY')
        self.secret_key = os.environ.get('NCP_SECRET_KEY')
        self.region = os.environ.get('NCP_REGION', 'KR')
        self.endpoint = os.environ.get('NCP_ENDPOINT', 'https://kr.object.ncloudstorage.com')
        self.bucket_name = os.environ.get('NCP_BUCKET_NAME', 'bus-data-storage')
        
        # S3 호환 클라이언트 생성
        self.client = boto3.client(
            's3',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
            endpoint_url=self.endpoint
        )
    
    def upload_file(self, file_path, object_key):
        """
        파일을 Object Storage에 업로드
        """
        try:
            self.client.upload_file(file_path, self.bucket_name, object_key)
            return True
        except ClientError as e:
            print(f"Object Storage 업로드 오류: {e}")
            return False
    
    def download_file(self, object_key, file_path):
        """
        Object Storage에서 파일 다운로드
        """
        try:
            self.client.download_file(self.bucket_name, object_key, file_path)
            return True
        except ClientError as e:
            print(f"Object Storage 다운로드 오류: {e}")
            return False
    
    def get_file_content(self, object_key):
        """
        Object Storage에서 파일 내용 가져오기
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=object_key)
            return response['Body'].read().decode('utf-8')
        except ClientError as e:
            print(f"Object Storage 파일 읽기 오류: {e}")
            return None


class BusDataCollector:
    """
    버스 데이터를 자동으로 수집하고 NCP Object Storage에 저장하는 클래스
    """
    
    def __init__(self, route_id="234001730", interval_minutes=2):
        self.route_id = route_id
        self.interval_seconds = interval_minutes * 60
        self.is_running = False
        self.thread = None
        self.data_dir = os.path.join(settings.BASE_DIR, 'bus_data')
        self.ncp_storage = NCPObjectStorage()
        
        # 데이터 저장 디렉토리 생성
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def collect_bus_data(self):
        """
        현재 시점의 버스 데이터를 수집
        """
        try:
            from .config import (
                GBIS_SERVICE_KEY, 
                GBIS_API_ENDPOINT, 
                API_TIMEOUT, 
                RESPONSE_FORMAT
            )
            
            # 서비스키 디코딩
            decoded_service_key = urllib.parse.unquote(GBIS_SERVICE_KEY)
            
            # API 요청 파라미터
            params = {
                'serviceKey': decoded_service_key,
                'routeId': self.route_id,
                'format': RESPONSE_FORMAT
            }
            
            # API 요청
            response = requests.get(GBIS_API_ENDPOINT, params=params, timeout=API_TIMEOUT)
            response.raise_for_status()
            
            # JSON 응답 파싱
            data = response.json()
            
            # 응답 데이터 처리
            response_data = data.get('response', {})
            msg_header = response_data.get('msgHeader', {})
            msg_body = response_data.get('msgBody', {})
            
            result_code = msg_header.get('resultCode')
            result_message = msg_header.get('resultMessage', '')
            query_time = msg_header.get('queryTime', 'N/A')
            
            if result_code == 0:
                bus_list = msg_body.get('busLocationList', [])
                
                # 수집된 데이터 구조화
                collected_data = {
                    'collection_time': datetime.now().isoformat(),
                    'buses': []
                }
                
                # 각 버스 데이터 처리 - 요청된 3개 필드만
                for bus in bus_list:
                    bus_data = {
                        'plateNo': bus.get('plateNo', 'N/A'),
                        'remainSeatCnt': bus.get('remainSeatCnt', -1),
                        'stationSeq': bus.get('stationSeq', 'N/A')
                    }
                    collected_data['buses'].append(bus_data)
                
                return collected_data
            else:
                return {
                    'collection_time': datetime.now().isoformat(),
                    'route_id': self.route_id,
                    'result_code': result_code,
                    'result_message': result_message,
                    'error': True
                }
                
        except Exception as e:
            return {
                'collection_time': datetime.now().isoformat(),
                'route_id': self.route_id,
                'error': True,
                'error_message': str(e)
            }
    
    def save_to_ncp_storage(self, data):
        """
        수집된 데이터를 NCP Object Storage에 저장
        """
        try:
            # 로컬 임시 파일에 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            local_filename = f"bus_data_{timestamp}.json"
            local_filepath = os.path.join(self.data_dir, local_filename)
            
            with open(local_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Object Storage에 업로드
            object_key = f"data/bus_data_{self.route_id}.json"
            upload_success = self.ncp_storage.upload_file(local_filepath, object_key)
            
            # 로컬 파일 삭제 (선택사항)
            if upload_success:
                os.remove(local_filepath)
                return object_key
            else:
                return local_filepath
            
        except Exception as e:
            print(f"NCP 저장 오류: {e}")
            return None
    
    def collect_and_save(self):
        """
        데이터 수집 및 저장 실행
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 버스 데이터 수집 시작 - 노선: {self.route_id}")
        
        data = self.collect_bus_data()
        result = self.save_to_ncp_storage(data)
        
        if result:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 데이터 저장 완료: {result}")
            if 'buses' in data:
                print(f"  - 수집된 버스 수: {len(data['buses'])}대")
                for bus in data['buses']:
                    print(f"    🚌 {bus['plateNo']} - 잔여좌석: {bus['remainSeatCnt']}개, 정류소순번: {bus['stationSeq']}")
        else:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 데이터 저장 실패")
    
    def start_collection(self):
        """
        자동 수집 시작
        """
        if self.is_running:
            print("이미 수집이 실행 중입니다.")
            return
        
        self.is_running = True
        
        def collection_loop():
            while self.is_running:
                self.collect_and_save()
                time.sleep(self.interval_seconds)
        
        self.thread = threading.Thread(target=collection_loop, daemon=True)
        self.thread.start()
        print(f"자동 데이터 수집 시작 - 노선: {self.route_id}, 간격: {self.interval_seconds//60}분")
    
    def stop_collection(self):
        """
        자동 수집 중지
        """
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("자동 데이터 수집 중지")
    
    def get_status(self):
        """
        수집 상태 반환
        """
        return {
            'is_running': self.is_running,
            'route_id': self.route_id,
            'interval_minutes': self.interval_seconds // 60,
            'storage_type': 'NCP Object Storage',
            'bucket_name': self.ncp_storage.bucket_name
        }


# 전역 수집기 인스턴스
bus_collector = BusDataCollector(route_id="234001730", interval_minutes=2)
