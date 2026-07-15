"""
공통 유틸리티 함수 모음
- 날씨 조회
- 날짜 문자열 정규화/변환
"""
import re
from datetime import datetime, timedelta, timezone

import requests


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
