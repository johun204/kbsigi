"""
공통 유틸리티 함수 모음
"""
import os
import json
import re
import requests
from datetime import datetime, timedelta, timezone

# -------------------- 공통 저장/판별 유틸 -------------------- #

def save_json(path, data):
	with open(path, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def _extract_items(response):
	try:
		if 'carousel' in response['template']['outputs'][0]:
			return response['template']['outputs'][0]['carousel']['items']
		if 'basicCard' in response['template']['outputs'][0]:
			return [response['template']['outputs'][0]['basicCard']]
		if 'textCard' in response['template']['outputs'][0]:
			return [response['template']['outputs'][0]['textCard']]
	except Exception:
		return []


def is_error_response(response):
	"""서버연결 실패 등 진짜 오류 응답인지 판별 (각 모듈에서 title을 '오류'로 통일)"""
	items = _extract_items(response)
	return any(item.get('title') == '오류' for item in items)


def is_no_data_response(response):
	"""오류는 아니지만 등록된 식단정보가 없는 경우"""
	items = _extract_items(response)
	return any('등록된 식단정보가 없습니다' in item.get('description', '') for item in items)


def _is_file_saved_today(path, now_kst):
	"""파일의 최종 수정 시각(mtime)이 오늘(KST) 날짜인지 확인한다.
	즉, '오늘 실행에서 이미 저장된(=최신) 데이터'인지를 판별한다."""
	if not os.path.exists(path):
		return False
	mtime = os.path.getmtime(path)
	file_dt_kst = datetime.fromtimestamp(mtime, tz=timezone.utc) + timedelta(hours=9)
	return file_dt_kst.date() == now_kst.date()


def is_file_content_error(path):
    if not os.path.exists(path):
        return True
        
    with open(path, 'r', encoding='utf-8') as f:
        file_data = json.load(f)
        
    return is_error_response(file_data)
	
def _is_file_content_identical(path, response_data):
    if not os.path.exists(path):
        return False
        
    with open(path, 'r', encoding='utf-8') as f:
        file_data = json.load(f)
        
    return file_data == response_data

def save_with_error_policy(path, response, now_kst):
	"""에러 응답 저장 정책에 따라 파일을 저장하거나 스킵한다.

	- 오류 응답 + 기존 파일이 '오늘' 저장된 것 -> 유지(스킵)
	- 오류 응답 + 기존 파일이 없거나 '어제 이전' 데이터 -> 오류로 덮어씀
	- 오류가 아닌 응답 -> 항상 저장
	"""
	if is_error_response(response):
		if is_file_content_error(path):
			print(f"[OVERWRITE-ERROR] {path}: 기존 파일 오류 응답 - 오류로 덮어씀")
			save_json(path, response)
			return True
		if _is_file_saved_today(path, now_kst):
			print(f"[SKIP] {path}: 오류 응답 - 오늘자 기존 파일 유지")
			return False
		if os.path.exists(path):
			print(f"[OVERWRITE-ERROR] {path}: 기존 파일이 어제 이전 데이터 - 오류로 덮어씀")
		else:
			print(f"[NEW-ERROR] {path}: 오류 응답 - 신규 저장")
		save_json(path, response)
		return True

	if _is_file_content_identical(path, response):
		print(f"{path}: 파일내용 변경없음 - 기존 파일 유지")
		return False
	print(f"{path}: 신규 저장")
	save_json(path, response)
	return True

def getWeather():
	temp = ''
	try:
		response = requests.request(
			'GET',
			'https://www.kr-weathernews.com/mv3/if/today.fcgi',
			params={'region': '1156011000'},
			timeout=5
		)
		jsondata = response.json()
		weather = jsondata['current']['wx']

		w = [
			['☀', '100', '104', '105'],
			['☁', '200'],
			['⛅', '101', '201'],
			['🌧', '102', '103', '202', '203', '300', '301', '302', '303', '304'],
			['🌨', '204', '205'],
		]
		for ww in w:
			for i in range(1, len(ww)):
				weather = weather.replace(ww[i], ww[0])
				if len(weather) == 1:
					break
			if len(weather) == 1:
				break

		if len(weather) > 1:
			weather = ''
		hour_num = int((datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%H"))
		temp = f'{("오전" if hour_num < 12 else "오후")} {(hour_num - 1) % 12 + 1}시 여의도 날씨는 {weather} {jsondata["current"]["temp"]}°C 입니다~'
	except Exception:
		pass
	return temp


def normalize_date_string(s: str) -> str:
	# 온점 개수 기준 판단
	if s.count('.') < 2:
		return s  # 일반 문자열

	# 숫자 + 온점으로 된 날짜 부분만 추출 (예: 26.1.19, 2026.01.19)
	match = re.search(r'(\d{2,4})\.(\d{1,2})\.(\d{1,2})', s)
	if not match:
		return s  # 날짜 패턴이 아니면 그대로 반환

	year, month, day = match.groups()

	# 연도 보정: 2자리 연도는 2000년대 기준
	if len(year) == 2:
		year = '20' + year

	return f"{year}{month.zfill(2)}{day.zfill(2)}"


def cvtDate(dt):
	days = ['일', '월', '화', '수', '목', '금', '토']
	return dt[4:6] + '.' + dt[6:8] + '(' + days[int(datetime(int(dt[0:4]), int(dt[4:6]), int(dt[6:8])).strftime('%w'))] + ')'
