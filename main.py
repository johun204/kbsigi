"""
GitHub Actions에서 실행되는 메인 스크립트
각 식당별 모듈을 호출하여 오늘/내일/모레 메뉴를 JSON 파일로 저장하고,
오늘자 메뉴를 표로 정리한 README.md를 생성한다.

[에러 응답 저장 정책]
1. 조회 함수가 오류 응답(서버연결 실패 등)을 반환했고, 해당 경로에 이미
   저장된 파일이 "오늘" 저장된 것이라면 -> 기존 파일을 유지하고 새로 저장하지 않는다.
2. 조회 함수가 오류 응답을 반환했는데 해당 경로에 파일이 없거나,
   있더라도 오늘 저장된 것이 아니라면(=어제 이전 데이터) -> 오류 응답으로 덮어쓴다.
3. 오류가 아닌 정상/데이터없음 응답은 항상 저장(덮어쓰기)한다.
"""
import json
import os
from datetime import datetime, timedelta, timezone

from common import getWeather
from hcafeteria import getHmenu
from ourhome import getOmenu
from kt import getKTmenu
from cjfresh import getFmenu


# -------------------- 공통 저장/판별 유틸 -------------------- #

def save_json(path, data):
	with open(path, 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=2)


def _extract_items(response):
	try:
		return response['template']['outputs'][0]['carousel']['items']
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


def get_status(response):
	"""README 표시용 상태 문자열 반환"""
	if is_error_response(response):
		return '❌ 오류'
	if is_no_data_response(response):
		return '⚠️ 데이터없음'
	return '✅ 정상'


def _is_file_saved_today(path, now_kst):
	"""파일의 최종 수정 시각(mtime)이 오늘(KST) 날짜인지 확인한다.
	즉, '오늘 실행에서 이미 저장된(=최신) 데이터'인지를 판별한다."""
	if not os.path.exists(path):
		return False
	mtime = os.path.getmtime(path)
	file_dt_kst = datetime.fromtimestamp(mtime, tz=timezone.utc) + timedelta(hours=9)
	return file_dt_kst.date() == now_kst.date()


def save_with_error_policy(path, response, now_kst):
	"""에러 응답 저장 정책에 따라 파일을 저장하거나 스킵한다.

	- 오류 응답 + 기존 파일이 '오늘' 저장된 것 -> 유지(스킵)
	- 오류 응답 + 기존 파일이 없거나 '어제 이전' 데이터 -> 오류로 덮어씀
	- 오류가 아닌 응답 -> 항상 저장
	"""
	if is_error_response(response):
		if _is_file_saved_today(path, now_kst):
			print(f"[SKIP] {path}: 오류 응답 - 오늘자 기존 파일 유지")
			return
		if os.path.exists(path):
			print(f"[OVERWRITE-ERROR] {path}: 기존 파일이 어제 이전 데이터 - 오류로 덮어씀")
		else:
			print(f"[NEW-ERROR] {path}: 오류 응답 - 신규 저장")
		save_json(path, response)
		return
	save_json(path, response)


# -------------------- README.md 생성 -------------------- #

def _sanitize_desc(desc):
	# 표 셀 안에서 줄바꿈/파이프 문자가 깨지지 않도록 치환
	return desc.replace('\n', '<br>').replace('|', '\\|').strip()


def _thumbnail_html(item, width=300):
	"""item에 thumbnail.imageUrl이 있으면 표 셀에 넣을 <img> 태그를 반환"""
	image_url = item.get('thumbnail', {}).get('imageUrl', '')
	if not image_url or image_url.find('johun204.github.io') > -1:
		return ''
	return f'<img src="{image_url}" width="{width}"><br>'


def _menu_rows(name, response):
	"""식당 하나에 대한 (식당명, 메뉴, 상태) 표 행 리스트 생성"""
	status = get_status(response)
	items = _extract_items(response)

	if not items:
		return [(name, '-', status)]

	rows = []
	for idx, item in enumerate(items):
		title = item.get('title', '')
		desc = _sanitize_desc(item.get('description', ''))
		thumb_html = _thumbnail_html(item)
		menu_cell = f"<b>{title}</b><br>{thumb_html}{desc}" if title else f"{thumb_html}<br>{desc}"
		# 첫 행에만 식당명을 표시하고, 나머지는 빈 값으로 두어 표를 깔끔하게 유지
		rows.append((name if idx == 0 else '', menu_cell, status if idx == 0 else ''))
	return rows


def build_readme(entries, weather_text, generated_at):
	lines = []
	lines.append('# 큽식이 <img src="https://johun204.github.io/kbsigi/image/logo.png" width="50">')
	lines.append('')
	lines.append(f'- 업데이트 시각: {generated_at}')


	for name, response in entries:
		lines.append('')
		lines.append('---')
		lines.append('')
		lines.append('<details>')
		lines.append(f'<summary><b>{name}</b> {get_status(response)}</summary>')
		lines.append('')
		if is_error_response(response) or is_no_data_response(response):
			pass
		else:
			for row_name, menu_cell, status in _menu_rows(name, response):
				lines.append(f'- {menu_cell}<br>')
		lines.append('</details>')
	lines.append('')
	lines.append('---')
	lines.append('')
	lines.append('> ✅ 정상 : 메뉴 정보를 정상적으로 불러왔습니다.<br>')
	lines.append('> ⚠️ 데이터없음 : 오류는 없었지만 등록된 식단정보가 없습니다.<br>')
	lines.append('> ❌ 오류 : 서버 연결/응답 오류로 메뉴를 불러오지 못했습니다.')
	lines.append('')

	return '\n'.join(lines)


# -------------------- 실행 -------------------- #

def main():
	now_kst = datetime.now(timezone.utc) + timedelta(hours=9)
	today_date = now_kst.strftime("%Y%m%d")
	after1_date = (now_kst + timedelta(days=1)).strftime("%Y%m%d")
	after2_date = (now_kst + timedelta(days=2)).strftime("%Y%m%d")

	os.makedirs('data', exist_ok=True)

	weather_text = getWeather()

	# default.json
	output = {
		"template": {
			"outputs": [{"simpleText": {"text": f"반가워요~!\n{weather_text}\n어떤곳의 식단을 알려드릴까요? (하하)\n\nex) 서관 메뉴 알려줘!\n내일 신관 밥 뭐나와?"}}],
			"quickReplies": [
				{"label": "전산센터", "action": "message", "messageText": "오늘 여의도전산센터(서관) 메뉴 알려줘~!"},
				{"label": "신관", "action": "message", "messageText": "오늘 KB국민은행 신관 메뉴 알려줘~!"},
				{"label": "본점", "action": "message", "messageText": "오늘 국민은행 본점 메뉴 알려줘~!"},
				{"label": "전경련", "action": "message", "messageText": "오늘 전경련회관 메뉴 알려줘~!"},
				{"label": "오늘의 운세", "action": "message", "messageText": "오늘의 운세 알려줘~!"},
			]
		},
		"version": "2.0"
	}
	save_json('data/default.json', output)

	# hcafeteria (여의도IT센터)
	hcafeteria_today = getHmenu(today_date, '173148')
	save_with_error_policy('data/hcafeteria.json', hcafeteria_today, now_kst)
	save_with_error_policy('data/hcafeteria_after1.json', getHmenu(after1_date, '173148'), now_kst)
	save_with_error_policy('data/hcafeteria_after2.json', getHmenu(after2_date, '173148'), now_kst)

	# ourhome1 (국민은행 신관)
	ourhome1_today = getOmenu(today_date, 'FA1MO')
	save_with_error_policy('data/ourhome1.json', ourhome1_today, now_kst)
	save_with_error_policy('data/ourhome1_after1.json', getOmenu(after1_date, 'FA1MO'), now_kst)
	save_with_error_policy('data/ourhome1_after2.json', getOmenu(after2_date, 'FA1MO'), now_kst)

	# ourhome2 (국민은행 본점)
	ourhome2_today = getOmenu(today_date, 'FAP56')
	save_with_error_policy('data/ourhome2.json', ourhome2_today, now_kst)
	save_with_error_policy('data/ourhome2_after1.json', getOmenu(after1_date, 'FAP56'), now_kst)
	save_with_error_policy('data/ourhome2_after2.json', getOmenu(after2_date, 'FAP56'), now_kst)

	# kt (KT)
	kt_today = getKTmenu(today_date)
	save_with_error_policy('data/kt.json', kt_today, now_kst)
	save_with_error_policy('data/kt_after1.json', getKTmenu(after1_date), now_kst)
	save_with_error_policy('data/kt_after2.json', getKTmenu(after2_date), now_kst)

	# cjfresh (전경련회관)
	cjfresh_1_today = getFmenu(today_date, '6083', '아침')
	cjfresh_2_today = getFmenu(today_date, '6083', '점심')
	cjfresh_3_today = getFmenu(today_date, '6083', '저녁')
	save_with_error_policy('data/cjfresh_1.json', cjfresh_1_today, now_kst)
	save_with_error_policy('data/cjfresh_2.json', cjfresh_2_today, now_kst)
	save_with_error_policy('data/cjfresh_3.json', cjfresh_3_today, now_kst)
	save_with_error_policy('data/cjfresh_1_after1.json', getFmenu(after1_date, '6083', '아침'), now_kst)
	save_with_error_policy('data/cjfresh_2_after1.json', getFmenu(after1_date, '6083', '점심'), now_kst)
	save_with_error_policy('data/cjfresh_3_after1.json', getFmenu(after1_date, '6083', '저녁'), now_kst)
	save_with_error_policy('data/cjfresh_1_after2.json', getFmenu(after2_date, '6083', '아침'), now_kst)
	save_with_error_policy('data/cjfresh_2_after2.json', getFmenu(after2_date, '6083', '점심'), now_kst)
	save_with_error_policy('data/cjfresh_3_after2.json', getFmenu(after2_date, '6083', '저녁'), now_kst)

	# -------------------- README.md 생성 (오늘자 메뉴 표) -------------------- #
	readme_entries = [
		('여의도IT센터', hcafeteria_today),
		('국민은행 신관', ourhome1_today),
		('국민은행 본점', ourhome2_today),
		('전경련회관', cjfresh_2_today),
	]

	generated_at = now_kst.strftime('%Y-%m-%d %H:%M') + ' (KST)'
	readme_content = build_readme(readme_entries, weather_text, generated_at)
	with open('README.md', 'w', encoding='utf-8') as f:
		f.write(readme_content)


if __name__ == "__main__":
	main()
