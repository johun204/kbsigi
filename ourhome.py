"""
아워홈 (국민은행 신관 / 본점) 메뉴 조회 모듈
"""
import json
import os

import requests

from common import cvtDate

OURHOME_KEY = os.getenv('OURHOME_KEY')
OURHOME_URL = os.getenv('OURHOME_URL')

LOCATION_NAMES = {
	'FA1MO': '국민은행 신관',
	'FAP56': '국민은행 본점',
}


def _buildQuickReplies(location_nm, BUSIPLCD):
	quickReplies = []
	quickReplies.append({'label': '오늘', 'action': 'message', 'messageText': f'오늘 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label': '내일', 'action': 'message', 'messageText': f'내일 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label': '모레', 'action': 'message', 'messageText': f'모레 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label': '처음으로', 'action': 'message', 'messageText': '처음으로'})

	if BUSIPLCD == 'FA1MO':
		quickReplies.append({'label': '오늘 본점', 'action': 'message', 'messageText': '오늘 국민은행 본점 메뉴 알려줘~!'})
	elif BUSIPLCD == 'FAP56':
		quickReplies.append({'label': '오늘 신관', 'action': 'message', 'messageText': '오늘 국민은행 신관 메뉴 알려줘~!'})

	return quickReplies


def _errorResponse(quickReplies, message):
	items = [{
		'title': '오류',
		'description': message,
		'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},
		'buttons': [
			{'action': 'webLink', 'label': 'Android 앱 설치', 'webLinkUrl': 'https://play.google.com/store/apps/details?id=com.ourhome.fsmobileticket'},
			{'action': 'webLink', 'label': 'iOS 앱 설치', 'webLinkUrl': 'https://apps.apple.com/kr/app/meal-care/id1182175084'},
		]
	}]
	return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}


def getOmenu(req_dt, BUSIPLCD='FA1MO'):
	location_nm = LOCATION_NAMES.get(BUSIPLCD, '')
	quickReplies = _buildQuickReplies(location_nm, BUSIPLCD)

	items = []
	imgYN = False

	try:
		data = json.loads(OURHOME_KEY)
		data['REQ_PARAMS']['BUSIPLCD'] = BUSIPLCD
		data['REQ_PARAMS']['MENU_DT'] = req_dt

		response = requests.request('POST', OURHOME_URL, data=json.dumps(data), timeout=5)
		jsondata = response.json()

		data = jsondata['returnList']
		for menu in data:
			if not menu['MEALCLASS_CD'] == '2':
				continue
			for corner in menu['CORNER_INFO']:
				KCAL = ''
				if 'KCAL' in corner:
					KCAL = ' (' + corner['KCAL'] + ' kcal)'
				desc_txt = corner['MENU_KOR'] + ' ✓\n' + corner['MENU_DTL_KOR'].replace(', ', ',').replace(' ,', ',').replace(',', '\n')
				if corner['MENU_IMG_NM'].find('http') > -1:
					items.append({
						'title': cvtDate(menu['MENU_DT']) + ' ' + location_nm + ' - ' + corner['CORNER_NM'] + KCAL,
						'description': desc_txt,
						'thumbnail': {'imageUrl': corner['MENU_IMG_NM']},
						'buttons': [{'action': 'webLink', 'label': '사진 크게보기', 'webLinkUrl': corner['MENU_IMG_NM']}]
					})
					imgYN = True
				else:
					items.append({
						'title': cvtDate(menu['MENU_DT']) + ' ' + location_nm + ' - ' + corner['CORNER_NM'] + KCAL,
						'description': desc_txt
					})

	except Exception as e:
		print(f"ourhome error: {str(e)}")
		return _errorResponse(quickReplies, '죄송합니다.\n아워홈 서버연결이 원활하지 않습니다. (흑흑)')

	if len(items) == 0:
		desc_txt = '등록된 식단정보가 없습니다.\n다른 날짜로 다시 물어봐주세요 (흑흑)'
		items.append({
			'title': cvtDate(req_dt) + ' ' + location_nm,
			'description': desc_txt,
			'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'}
		})
		return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}

	if imgYN:
		for i in range(len(items)):
			if 'thumbnail' not in items[i]:
				items[i]['thumbnail'] = {'imageUrl': 'https://johun204.github.io/kbsigi/image/no_image.png'}
			items[i]['description'] = items[i]['description'].strip().replace('\n', ',').replace(' ✓', '')
		return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}

	return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'textCard', 'items': items}}], 'quickReplies': quickReplies}}
