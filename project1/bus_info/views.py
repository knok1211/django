from .data_collector import bus_collector
import os
import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


@csrf_exempt
@require_http_methods(["GET"])
def get_bus_seat_info(request):
    """
    GBIS API를 사용하여 버스의 잔여 좌석수를 조회하는 뷰
    """
    # 요청 파라미터에서 routeId 가져오기
    route_id = request.GET.get('routeId')
    
    if not route_id:
        return JsonResponse({
            'error': 'routeId 파라미터가 필요합니다.',
            'example': '/api/bus-seat/?routeId=233000031'
        }, status=400)
    
    # 서비스키 확인
    if GBIS_SERVICE_KEY == "YOUR_SERVICE_KEY_HERE":
        return JsonResponse({
            'error': 'GBIS API 서비스키가 설정되지 않았습니다.',
            'instruction': 'bus_info/config.py 파일에서 GBIS_SERVICE_KEY를 실제 서비스키로 설정해주세요.',
            'link': 'https://data.go.kr에서 발급받을 수 있습니다.'
        }, status=400)
    
    # 서비스키 디코딩
    decoded_service_key = urllib.parse.unquote(GBIS_SERVICE_KEY)
    
    # API 요청 파라미터
    params = {
        'serviceKey': decoded_service_key,
        'routeId': route_id,
        'format': RESPONSE_FORMAT
    }
    
    try:
        # API 요청
        response = requests.get(GBIS_API_ENDPOINT, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        # 응답 내용 확인
        response_text = response.text
        if not response_text.strip():
            return JsonResponse({
                'error': 'API에서 빈 응답을 받았습니다.',
                'status_code': response.status_code,
                'request_url': response.url,
                'response_headers': dict(response.headers)
            }, status=400)
        
        # JSON 응답 파싱
        try:
            data = response.json()
        except json.JSONDecodeError as json_error:
            return JsonResponse({
                'error': 'API 응답이 JSON 형식이 아닙니다.',
                'json_error': str(json_error),
                'response_text': response_text[:500],  # 처음 500자만
                'status_code': response.status_code,
                'request_url': response.url
            }, status=400)
        
        # 응답 데이터 처리 - GBIS API 구조에 맞게 파싱
        response_data = data.get('response', {})
        msg_header = response_data.get('msgHeader', {})
        msg_body = response_data.get('msgBody', {})
        
        result_code = msg_header.get('resultCode')
        result_message = msg_header.get('resultMessage', '')
        query_time = msg_header.get('queryTime', 'N/A')
        
        if result_code == 0:
            bus_list = msg_body.get('busLocationList', [])
            
            # 버스별 좌석 정보 추출
            seat_info = []
            for bus in bus_list:
                seat_data = {
                    'plateNo': bus.get('plateNo', 'N/A'),
                    'vehId': bus.get('vehId', 'N/A'),
                    'routeId': bus.get('routeId', route_id),
                    'remainSeatCnt': bus.get('remainSeatCnt', -1),
                    'crowded': bus.get('crowded', 'N/A'),
                    'routeTypeCd': bus.get('routeTypeCd', 'N/A'),
                    'lowPlate': bus.get('lowPlate', 0),
                    'stationId': bus.get('stationId', 'N/A'),
                    'stationSeq': bus.get('stationSeq', 'N/A'),
                    'stateCd': bus.get('stateCd', 'N/A'),
                    'taglessCd': bus.get('taglessCd', 0)
                }
                
                # 좌석수 해석
                if seat_data['remainSeatCnt'] == -1:
                    seat_data['seatInfo'] = "좌석수 정보 없음"
                else:
                    seat_data['seatInfo'] = f"잔여 좌석: {seat_data['remainSeatCnt']}개"
                
                # 혼잡도 해석
                crowded_map = {
                    1: "여유",
                    2: "보통", 
                    3: "혼잡",
                    4: "매우혼잡"
                }
                if isinstance(seat_data['crowded'], int):
                    seat_data['crowdedInfo'] = crowded_map.get(seat_data['crowded'], "정보없음")
                else:
                    seat_data['crowdedInfo'] = "정보없음"
                
                # 저상버스 여부
                low_plate_map = {
                    0: "일반버스",
                    1: "저상버스",
                    2: "2층버스"
                }
                seat_data['busType'] = low_plate_map.get(seat_data['lowPlate'], "일반버스")
                
                # 상태 해석
                state_map = {
                    0: "교차로통과",
                    1: "정류소도착",
                    2: "정류소출발"
                }
                seat_data['stateInfo'] = state_map.get(seat_data['stateCd'], "정보없음")
                
                seat_info.append(seat_data)
            
            return JsonResponse({
                'success': True,
                'routeId': route_id,
                'queryTime': query_time,
                'resultMessage': result_message,
                'busCount': len(seat_info),
                'busList': seat_info
            })
        else:
            return JsonResponse({
                'error': 'API 요청 실패',
                'resultCode': result_code,
                'resultMessage': result_message,
                'rawResponse': data  # 디버깅을 위한 원본 응답 포함
            }, status=400)
            
    except requests.exceptions.RequestException as e:
        return JsonResponse({
            'error': 'API 요청 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=500)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'error': 'API 응답을 파싱하는 중 오류가 발생했습니다.',
            'detail': str(e)
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': '예상치 못한 오류가 발생했습니다.',
            'detail': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_route_info(request):
    """
    노선 정보를 조회하는 뷰 (예시)
    """
    return JsonResponse({
        'message': '버스 좌석수 조회 API',
        'usage': {
            'endpoint': '/api/bus-seat/',
            'parameter': 'routeId (필수)',
            'example': '/api/bus-seat/?routeId=233000031'
        },
        'note': '실제 사용시에는 공공데이터포털에서 발급받은 서비스키가 필요합니다.'
    })


def home(request):
    """
    홈페이지 뷰
    """
    return render(request, 'bus_info/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def start_data_collection(request):
    """
    자동 데이터 수집 시작
    """
    try:
        bus_collector.start_collection()
        return JsonResponse({
            'success': True,
            'message': '자동 데이터 수집이 시작되었습니다.',
            'status': bus_collector.get_status()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def stop_data_collection(request):
    """
    자동 데이터 수집 중지
    """
    try:
        bus_collector.stop_collection()
        return JsonResponse({
            'success': True,
            'message': '자동 데이터 수집이 중지되었습니다.',
            'status': bus_collector.get_status()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_collection_status(request):
    """
    데이터 수집 상태 조회
    """
    try:
        status = bus_collector.get_status()
        
        # 저장된 파일 정보 포함
        data_dir = status['data_directory']
        main_file = f"bus_data_{bus_collector.route_id}.json"
        main_filepath = os.path.join(data_dir, main_file)
        
        status['main_file'] = main_file
        status['file_exists'] = os.path.exists(main_filepath)
        
        # 파일이 있으면 수집 횟수 확인
        if status['file_exists']:
            try:
                with open(main_filepath, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                status['collection_count'] = len(file_data.get('collections', []))
                status['last_updated'] = file_data.get('last_updated', 'N/A')
            except:
                status['collection_count'] = 0
                status['last_updated'] = 'N/A'
        else:
            status['collection_count'] = 0
            status['last_updated'] = 'N/A'
        
        return JsonResponse({
            'success': True,
            'status': status
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def collect_data_once(request):
    """
    한 번만 데이터 수집 실행
    """
    try:
        bus_collector.collect_and_save()
        return JsonResponse({
            'success': True,
            'message': '데이터 수집이 완료되었습니다.',
            'status': bus_collector.get_status()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_latest_data(request):
    """
    최신 수집 데이터 조회
    """
    try:
        status = bus_collector.get_status()
        data_dir = status['data_directory']
        
        # 메인 파일에서 최신 데이터 조회
        main_file = f"bus_data_{bus_collector.route_id}.json"
        main_filepath = os.path.join(data_dir, main_file)
        
        if os.path.exists(main_filepath):
            with open(main_filepath, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
            
            collections = file_data.get('collections', [])
            if collections:
                latest = collections[-1]  # 가장 최신 데이터
                return JsonResponse({
                    'success': True,
                    'data': latest,
                    'total_collections': len(collections),
                    'last_updated': file_data.get('last_updated', 'N/A')
                })
        
        return JsonResponse({
            'success': False,
            'message': '수집된 데이터가 없습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def download_data_file(request):
    """
    특정 데이터 파일 다운로드
    """
    try:
        filename = request.GET.get('filename')
        if not filename:
            return JsonResponse({
                'success': False,
                'error': '파일명이 필요합니다.'
            }, status=400)
        
        status = bus_collector.get_status()
        data_dir = status['data_directory']
        filepath = os.path.join(data_dir, filename)
        
        if not os.path.exists(filepath):
            return JsonResponse({
                'success': False,
                'error': '파일을 찾을 수 없습니다.'
            }, status=404)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        response = HttpResponse(content, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def test_api_connection(request):
    """
    API 연결 테스트용 뷰
    """
    route_id = request.GET.get('routeId', '233000031')
    
    # 서비스키 디코딩
    decoded_service_key = urllib.parse.unquote(GBIS_SERVICE_KEY)
    
    # API 요청 파라미터
    params = {
        'serviceKey': decoded_service_key,
        'routeId': route_id,
        'format': RESPONSE_FORMAT
    }
    
    try:
        # API 요청
        response = requests.get(GBIS_API_ENDPOINT, params=params, timeout=API_TIMEOUT)
        
        response_text = response.text
        
        # JSON 파싱 시도
        json_data = None
        json_error = None
        try:
            json_data = response.json()
        except json.JSONDecodeError as e:
            json_error = str(e)
        
        return JsonResponse({
            'success': True,
            'status_code': response.status_code,
            'request_url': response.url,
            'response_headers': dict(response.headers),
            'response_text': response_text[:1000],  # 처음 1000자만
            'response_length': len(response_text),
            'json_parsed': json_data is not None,
            'json_error': json_error,
            'json_data': json_data,
            'params_used': params,
            'decoded_service_key': decoded_service_key
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'params_used': params
        }, status=500)
