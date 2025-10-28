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
        
        # 오늘 날짜로 파일명 생성
        from datetime import datetime
        today_date = datetime.now().strftime('%Y-%m-%d')
        today_file = f"bus_data_{bus_collector.route_id}_{today_date}.json"
        today_filepath = os.path.join(data_dir, today_file)
        
        # 모든 파일 조회
        pattern = os.path.join(data_dir, f"bus_data_{bus_collector.route_id}_*.json")
        all_files = glob.glob(pattern)
        
        # 오늘 파일이 없으면 가장 최근 파일을 찾기
        latest_file_date = None
        if all_files:
            # 파일명으로 정렬하여 가장 최근 파일 찾기
            all_files.sort()
            latest_file = all_files[-1]
            filename = os.path.basename(latest_file)
            # bus_data_234001730_2025-10-28.json에서 날짜 부분 추출
            parts = filename.replace('.json', '').split('_')
            if len(parts) >= 3:
                latest_file_date = parts[2]
        
        # 오늘 파일이 없으면 최신 파일 정보를 사용
        if not os.path.exists(today_filepath) and latest_file_date:
            today_file = f"bus_data_{bus_collector.route_id}_{latest_file_date}.json"
            today_filepath = os.path.join(data_dir, today_file)
        
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
        
        # 페이지네이션 파라미터
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 10))
        
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
        
        # 페이지네이션 적용
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_files = file_list[start_idx:end_idx]
        
        total_pages = (len(file_list) + per_page - 1) // per_page
        
        status['file_list'] = paginated_files
        status['pagination'] = {
            'current_page': page,
            'per_page': per_page,
            'total_files': len(file_list),
            'total_pages': total_pages,
            'has_previous': page > 1,
            'has_next': page < total_pages
        }
        
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


@csrf_exempt
@require_http_methods(["GET"])
def download_all_files(request):
    """
    모든 데이터 파일을 ZIP으로 압축하여 다운로드
    """
    try:
        import zipfile
        from io import BytesIO
        from datetime import datetime
        import glob
        
        status = bus_collector.get_status()
        data_dir = status['data_directory']
        
        # 모든 JSON 파일 찾기
        pattern = os.path.join(data_dir, f"bus_data_{bus_collector.route_id}_*.json")
        all_files = glob.glob(pattern)
        
        if not all_files:
            return JsonResponse({
                'success': False,
                'error': '다운로드할 파일이 없습니다.'
            }, status=404)
        
        # ZIP 파일 생성
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filepath in all_files:
                filename = os.path.basename(filepath)
                zip_file.write(filepath, filename)
        
        zip_buffer.seek(0)
        
        # 현재 날짜로 ZIP 파일명 생성
        current_date = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        zip_filename = f'bus_data_all_{current_date}.zip'
        
        response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)



