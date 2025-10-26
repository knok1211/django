import json
import os
import threading
import time
from datetime import datetime, time as dt_time
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
    
    def is_skip_time(self, query_time_str):
        """
        쿼리 시간이 00:00 ~ 05:30 범위인지 확인
        """
        try:
            if query_time_str == 'N/A':
                return False
            
            # query_time 형식: "2024-01-01 12:00:00" 또는 "2024-01-01 12:00:00.123"
            # 밀리초 부분이 있으면 제거
            if '.' in query_time_str:
                query_time_str = query_time_str.split('.')[0]
            
            query_datetime = datetime.strptime(query_time_str, '%Y-%m-%d %H:%M:%S')
            query_time = query_datetime.time()
            
            # 00:00 ~ 05:30 범위 확인
            skip_start = dt_time(0, 0)  # 00:00
            skip_end = dt_time(5, 30)   # 05:30
            
            return skip_start <= query_time <= skip_end
            
        except Exception as e:
            print(f"시간 파싱 오류: {e}")
            return False
    
    def get_date_from_query_time(self, query_time_str):
        """
        쿼리 시간에서 날짜 추출 (YYYY-MM-DD 형식)
        """
        try:
            if query_time_str == 'N/A':
                return datetime.now().strftime('%Y-%m-%d')
            
            # query_time 형식: "2024-01-01 12:00:00" 또는 "2024-01-01 12:00:00.123"
            # 밀리초 부분이 있으면 제거
            if '.' in query_time_str:
                query_time_str = query_time_str.split('.')[0]
            
            query_datetime = datetime.strptime(query_time_str, '%Y-%m-%d %H:%M:%S')
            return query_datetime.strftime('%Y-%m-%d')
            
        except Exception as e:
            print(f"날짜 파싱 오류: {e}")
            return datetime.now().strftime('%Y-%m-%d')

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
            
            # 00:00 ~ 05:30 시간대 체크
            if self.is_skip_time(query_time):
                return {
                    'query_time': query_time,
                    'skipped': True,
                    'skip_reason': '00:00 ~ 05:30 시간대는 수집하지 않습니다.'
                }
            
            if result_code == 0:
                bus_list = msg_body.get('busLocationList', [])
                
                # 수집된 데이터 구조화
                collected_data = {
                    'query_time': query_time,
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
                    'query_time': query_time,
                    'route_id': self.route_id,
                    'result_code': result_code,
                    'result_message': result_message,
                    'error': True
                }
                
        except Exception as e:
            return {
                'query_time': 'N/A',
                'route_id': self.route_id,
                'error': True,
                'error_message': str(e)
            }
    
    def save_to_json(self, data):
        """
        수집된 데이터를 날짜별 JSON 파일에 저장
        """
        try:
            # 쿼리 시간에서 날짜 추출
            date_str = self.get_date_from_query_time(data.get('query_time', 'N/A'))
            
            # 날짜별 파일명 생성
            filename = f"bus_data_{self.route_id}_{date_str}.json"
            filepath = os.path.join(self.data_dir, filename)
            
            # 기존 파일이 있으면 읽어서 업데이트
            existing_data = {
                'route_id': self.route_id,
                'date': date_str,
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
            
            # 하루 최대 1000개 수집 데이터 유지 (파일 크기 관리)
            if len(existing_data['collections']) > 1000:
                existing_data['collections'] = existing_data['collections'][-1000:]
            
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
        
        # 수집 건너뛰기 체크
        if data.get('skipped'):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 수집 건너뜀: {data.get('skip_reason')}")
            print(f"  - 쿼리 시간: {data.get('query_time')}")
            return None
        
        filepath = self.save_to_json(data)
        
        if filepath:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 데이터 저장 완료: {filepath}")
            if 'buses' in data:
                print(f"  - 쿼리 시간: {data.get('query_time')}")
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
