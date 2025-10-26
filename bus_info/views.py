from .data_collector import bus_collector
import os
import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods





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
        from datetime import datetime
        import glob
        
        status = bus_collector.get_status()
        data_dir = status['data_directory']
        
        # 최신 수집 데이터 기준 날짜 파일 확인
        # 모든 파일을 먼저 조회하여 가장 최근 파일 찾기
        pattern = os.path.join(data_dir, f"bus_data_{bus_collector.route_id}_*.json")
        all_files = glob.glob(pattern)
        
        current_date_str = None
        if all_files:
            # 파일명으로 정렬하여 가장 최근 파일의 날짜 추출
            all_files.sort()
            latest_file = all_files[-1]
            filename = os.path.basename(latest_file)
            # bus_data_234001730_2025-10-26.json에서 날짜 부분 추출
            parts = filename.split('_')
            if len(parts) >= 3:
                current_date_str = parts[2].replace('.json', '')
        
        # 현재 날짜 기준 파일 설정
        if current_date_str:
            today_file = f"bus_data_{bus_collector.route_id}_{current_date_str}.json"
            today_filepath = os.path.join(data_dir, today_file)
        else:
            # 파일이 없는 경우 기본값
            today_file = f"bus_data_{bus_collector.route_id}_no-data.json"
            today_filepath = ""
        
        status['today_file'] = today_file
        status['today_file_exists'] = os.path.exists(today_filepath) if today_filepath else False
        status['total_files'] = len(all_files)
        
        # 오늘 파일이 있으면 수집 횟수 확인
        if status['today_file_exists']:
            try:
                with open(today_filepath, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                collections = file_data.get('collections', [])
                status['collection_count'] = len(collections)
                
                # 마지막 수집 데이터의 queryTime 사용
                if collections:
                    last_collection = collections[-1]
                    status['last_updated'] = last_collection.get('query_time', 'N/A')
                else:
                    status['last_updated'] = 'N/A'
            except:
                status['collection_count'] = 0
                status['last_updated'] = 'N/A'
        else:
            # 오늘 파일이 없으면 가장 최근 파일에서 확인
            if all_files:
                # 파일명으로 정렬하여 가장 최근 파일 찾기
                all_files.sort()
                latest_file = all_files[-1]
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        file_data = json.load(f)
                    collections = file_data.get('collections', [])
                    if collections:
                        last_collection = collections[-1]
                        status['last_updated'] = last_collection.get('query_time', 'N/A')
                        status['collection_count'] = len(collections)
                    else:
                        status['last_updated'] = 'N/A'
                        status['collection_count'] = 0
                except:
                    status['collection_count'] = 0
                    status['last_updated'] = 'N/A'
            else:
                status['collection_count'] = 0
                status['last_updated'] = 'N/A'
        
        # 파일 목록 정보 추가
        file_list = []
        for filepath in sorted(all_files, reverse=True):  # 최신순 정렬
            filename = os.path.basename(filepath)
            file_size = os.path.getsize(filepath)
            file_list.append({
                'filename': filename,
                'size': file_size,
                'size_mb': round(file_size / 1024 / 1024, 2)
            })
        
        status['file_list'] = file_list[:10]  # 최근 10개 파일만
        
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
        from datetime import datetime
        import glob
        
        status = bus_collector.get_status()
        data_dir = status['data_directory']
        
        # 모든 날짜별 파일 목록 조회
        pattern = os.path.join(data_dir, f"bus_data_{bus_collector.route_id}_*.json")
        all_files = glob.glob(pattern)
        
        if not all_files:
            return JsonResponse({
                'success': False,
                'message': '수집된 데이터가 없습니다.'
            })
        
        # 파일명으로 정렬하여 가장 최근 파일 찾기
        all_files.sort()
        latest_file = all_files[-1]
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        
        collections = file_data.get('collections', [])
        if collections:
            latest = collections[-1]  # 가장 최신 데이터
            return JsonResponse({
                'success': True,
                'data': latest,
                'total_collections': len(collections),
                'file_date': file_data.get('date', 'N/A'),
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



