import json
import os
from datetime import datetime, timedelta, timezone

from common import getWeather, is_error_response, is_no_data_response, save_json, save_with_error_policy, is_file_content_error, _extract_items
#from hcafeteria import getHmenu
from ourhome import getOmenu
from kt import getKTmenu
from cjfresh import getFmenu

from kbsigi_ai import kbsigi_pick_with_ai

# -------------------- README.md 생성 -------------------- #
def get_status(response):
	"""README 표시용 상태 문자열 반환"""
	if is_error_response(response):
		return '❌ 오류'
	if is_no_data_response(response):
		return '⚠️ 데이터없음'
	return '✅ 정상'

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
				{"label": "The-K", "action": "message", "messageText": "오늘 교직원공제회(The-K) 메뉴 알려줘~!"},
				{"label": "오늘의 운세", "action": "message", "messageText": "오늘의 운세 알려줘~!"},
			]
		},
		"version": "2.0"
	}
	save_json('data/default.json', output)

	# ourhome1 (국민은행 신관)
	ourhome1_today = getOmenu(today_date, 'FA1MO')
	if save_with_error_policy('data/ourhome1.json', ourhome1_today, now_kst) or is_file_content_error('data/ourhome1_ai.json'):
		ourhome1_ai = kbsigi_pick_with_ai(ourhome1_today)
		save_with_error_policy('data/ourhome1_ai.json', ourhome1_ai, now_kst)
	save_with_error_policy('data/ourhome1_after1.json', getOmenu(after1_date, 'FA1MO'), now_kst)
	save_with_error_policy('data/ourhome1_after2.json', getOmenu(after2_date, 'FA1MO'), now_kst)

	# ourhome2 (국민은행 본점)
	ourhome2_today = getOmenu(today_date, 'FAP56')
	if save_with_error_policy('data/ourhome2.json', ourhome2_today, now_kst) or is_file_content_error('data/ourhome2_ai.json'):
		ourhome2_ai = kbsigi_pick_with_ai(ourhome2_today)
		save_with_error_policy('data/ourhome2_ai.json', ourhome2_ai, now_kst)
	save_with_error_policy('data/ourhome2_after1.json', getOmenu(after1_date, 'FAP56'), now_kst)
	save_with_error_policy('data/ourhome2_after2.json', getOmenu(after2_date, 'FAP56'), now_kst)

	# kt (KT)
	kt_today = getKTmenu(today_date)
	save_with_error_policy('data/kt.json', kt_today, now_kst)
	save_with_error_policy('data/kt_after1.json', getKTmenu(after1_date), now_kst)
	save_with_error_policy('data/kt_after2.json', getKTmenu(after2_date), now_kst)

	# cjfresh (전경련회관)
	cjfresh1a_today = getFmenu(today_date, '6083', '아침')
	cjfresh1b_today = getFmenu(today_date, '6083', '점심')
	cjfresh1c_today = getFmenu(today_date, '6083', '저녁')
	save_with_error_policy('data/cjfresh1a.json', cjfresh1a_today, now_kst)
	if save_with_error_policy('data/cjfresh1b.json', cjfresh1b_today, now_kst) or is_file_content_error('data/cjfresh1b_ai.json'):
		cjfresh1b_ai = kbsigi_pick_with_ai(cjfresh1b_today)
		save_with_error_policy('data/cjfresh1b_ai.json', cjfresh1b_ai, now_kst)
	save_with_error_policy('data/cjfresh1c.json', cjfresh1c_today, now_kst)
	save_with_error_policy('data/cjfresh1a_after1.json', getFmenu(after1_date, '6083', '아침'), now_kst)
	save_with_error_policy('data/cjfresh1b_after1.json', getFmenu(after1_date, '6083', '점심'), now_kst)
	save_with_error_policy('data/cjfresh1c_after1.json', getFmenu(after1_date, '6083', '저녁'), now_kst)
	save_with_error_policy('data/cjfresh1a_after2.json', getFmenu(after2_date, '6083', '아침'), now_kst)
	save_with_error_policy('data/cjfresh1b_after2.json', getFmenu(after2_date, '6083', '점심'), now_kst)
	save_with_error_policy('data/cjfresh1c_after2.json', getFmenu(after2_date, '6083', '저녁'), now_kst)

	# cjfresh (한국교직원공제회)
	cjfresh2_today = getFmenu(today_date, '6848')
	if save_with_error_policy('data/cjfresh2.json', cjfresh2_today, now_kst) or is_file_content_error('data/cjfresh2_ai.json'):
		cjfresh2_ai = kbsigi_pick_with_ai(cjfresh2_today)
		save_with_error_policy('data/cjfresh2_ai.json', cjfresh2_ai, now_kst)
	save_with_error_policy('data/cjfresh2_after1.json', getFmenu(after1_date, '6848'), now_kst)
	save_with_error_policy('data/cjfresh2_after2.json', getFmenu(after2_date, '6848'), now_kst)

	# hcafeteria >> cjfreshmeal (여의도IT센터)
	cjfresh3_today = getFmenu(today_date, '7169')
	if save_with_error_policy('data/cjfresh3.json', cjfresh3_today, now_kst) or is_file_content_error('data/cjfresh3_ai.json'):
		cjfresh3_ai = kbsigi_pick_with_ai(cjfresh3_today)
		save_with_error_policy('data/cjfresh3_ai.json', cjfresh3_ai, now_kst)
	save_with_error_policy('data/cjfresh3_after1.json', getFmenu(after1_date, '7169'), now_kst)
	save_with_error_policy('data/cjfresh3_after2.json', getFmenu(after2_date, '7169'), now_kst)
	
	# -------------------- README.md 생성 (오늘자 메뉴 표) -------------------- #
	readme_entries = [
		('여의도IT센터', cjfresh3_today),
		('국민은행 신관', ourhome1_today),
		('국민은행 본점', ourhome2_today),
		('전경련회관', cjfresh1b_today),
		('한국교직원공제회', cjfresh2_today),
	]

	generated_at = now_kst.strftime('%Y-%m-%d %H:%M') + ' (KST)'
	readme_content = build_readme(readme_entries, weather_text, generated_at)
	with open('README.md', 'w', encoding='utf-8') as f:
		f.write(readme_content)


if __name__ == "__main__":
	main()
