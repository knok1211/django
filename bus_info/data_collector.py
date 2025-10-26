import json
import os
import threading
import time
from datetime import datetime
from django.conf import settings
from .config import (
    GBIS_SERVICE_KEY, 
    GBIS_API_ENDPOINT, 
    API_TIMEOUT, 
    RESPONSE_FORMAT
)
import requests
import urllib.parse


class BusDataCollector:
    """
    버스 데이터를 자동으로 수집하고 JSON 파일에 저장하는 클래스
    """
    
    def __init__(self, route_id="234001730", interval_minutes=2):
        self.route_id = route_id
        self.interval_seconds = interval_minutes * 60
        self.is_running = False
        self.thread = None
        self.data_dir = os.path.join(settings.BASE_DIR, 'bus_data')
        
        # 데이터 저장 디렉토리 생성
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def collect_bus_data(self):
        """
        현재 시점의 버스 데이터를 수집
        """
        try:
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
                    #'collection_time': datetime.now().isoformat(),
                    'query_time': query_time,
                    #'route_id': self.route_id,
                    #'result_code': result_code,
                    #'result_message': result_message,
                    #'bus_count': len(bus_list),
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
    
    def save_to_json(self, data):
        """
        수집된 데이터를 JSON 파일에 저장 (기존 파일 업데이트)
        """
        try:
            # 고정 파일명 사용 (업데이트 방식)
            filename = f"bus_data_{self.route_id}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            # 기존 파일이 있으면 읽어서 업데이트
            existing_data = {
                'route_id': self.route_id,
                'last_updated': datetime.now().isoformat(),
                'collections': []
            }
            
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except:
                    pass  # 파일이 손상된 경우 새로 시작
            
            # 새 수집 데이터 추가
            existing_data['last_updated'] = datetime.now().isoformat()
            existing_data['collections'].append(data)
            
            # 최근 500개 수집 데이터만 유지 (파일 크기 관리)
            if len(existing_data['collections']) > 500:
                existing_data['collections'] = existing_data['collections'][-500:]
            
            # 업데이트된 파일 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
            
            return filepath
            
        except Exception as e:
            print(f"JSON 저장 오류: {e}")
            return None
    
    def collect_and_save(self):
        """
        데이터 수집 및 저장 실행
        """
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 버스 데이터 수집 시작 - 노선: {self.route_id}")
        
        data = self.collect_bus_data()
        filepath = self.save_to_json(data)
        
        if filepath:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 데이터 저장 완료: {filepath}")
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
            'data_directory': self.data_dir
        }


# 전역 수집기 인스턴스
bus_collector = BusDataCollector(route_id="234001730", interval_minutes=2)

