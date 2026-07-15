"""
CJ프레시밀 (전경련회관) 메뉴 조회 모듈
"""
import os

import requests

from common import cvtDate

CJFRESH_URL = os.getenv('CJFRESH_URL')
CJFRESH_URL2 = os.getenv('HOME_URL') + '/cjfreshmeal'

STORE_NAMES = {
	'6083': '전경련회관',
}


def _resolveMealType(txt):
	dataType, dataName = '2', '중식'
	if txt.find('아침') > -1 or txt.find('조식') > -1:
		dataType, dataName = '1', '조식'
	elif txt.find('점심') > -1 or txt.find('중식') > -1:
		dataType, dataName = '2', '중식'
	elif txt.find('저녁') > -1 or txt.find('석식') > -1:
		dataType, dataName = '3', '석식'
	return dataType, dataName


def _buildQuickReplies(location_nm, dataName):
	quickReplies = []
	quickReplies.append({'label': '조식', 'action': 'message', 'messageText': f'오늘 {location_nm} 조식 메뉴 알려줘~!'})
	quickReplies.append({'label': '중식', 'action': 'message', 'messageText': f'오늘 {location_nm} 중식 메뉴 알려줘~!'})
	quickReplies.append({'label': '석식', 'action': 'message', 'messageText': f'오늘 {location_nm} 석식 메뉴 알려줘~!'})
	quickReplies.append({'label': '내일', 'action': 'message', 'messageText': f'내일 {location_nm} {dataName} 메뉴 알려줘~!'})
	quickReplies.append({'label': 'KT(구내식당)', 'action': 'message', 'messageText': '오늘 KT 메뉴 알려줘~!'})
	quickReplies.append({'label': '처음으로', 'action': 'message', 'messageText': '처음으로'})
	return quickReplies


def _errorResponse(quickReplies, message):
	items = [{
		'title': '오류',
		'description': message,
		'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},
		'buttons': [
			{'action': 'webLink', 'label': 'Android 앱 설치', 'webLinkUrl': 'https://play.google.com/store/apps/details?id=com.cjfreshway.fs.freshmeal'},
			{'action': 'webLink', 'label': 'iOS 앱 설치', 'webLinkUrl': 'https://apps.apple.com/kr/app/id1594764668'},
		]
	}]
	return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}


def getFmenu(req_dt, storeIdx, txt):
	location_nm = STORE_NAMES.get(storeIdx, '')
	dataType, dataName = _resolveMealType(txt)
	quickReplies = _buildQuickReplies(location_nm, dataName)

	items = []
	imgYN = False

	try:
		response = requests.request('GET', f'{CJFRESH_URL2}?storeIdx={storeIdx}&weekType=1', timeout=10)
		jsondata = response.json()

		if 'data' in jsondata and len(jsondata['data']) > 0:
			for x in jsondata['data']:
				if dataType in jsondata['data'][x] and len(jsondata['data'][x][dataType]) > 0:
					for menu in jsondata['data'][x][dataType]:
						if req_dt == menu['mealDt']:
							if 'thumbnailUrl' in menu and menu['thumbnailUrl'] != "":
								items.append({
									'title': cvtDate(menu['mealDt']) + ' ' + location_nm + ' - ' + menu['corner'] + '(' + dataName + ')',
									'description': menu['name'] + '\n' + ('-' if menu['side'] is None else menu['side']),
									'thumbnail': {'imageUrl': menu['thumbnailUrl']},
									'buttons': [{'action': 'webLink', 'label': '사진 크게보기', 'webLinkUrl': menu['thumbnailUrl']}]
								})
								imgYN = True
							else:
								items.append({
									'title': cvtDate(menu['mealDt']) + ' ' + location_nm + ' - ' + menu['corner'] + '(' + dataName + ')',
									'description': menu['name'] + '\n' + ('-' if menu['side'] is None else menu['side'])
								})

		if len(items) == 0:
			items.append({
				'title': cvtDate(req_dt) + ' ' + location_nm + ' - ' + dataName,
				'description': '등록된 식단정보가 없습니다.\n다른 날짜로 다시 물어봐주세요 (흑흑)\n\nex) 서관 메뉴 알려줘!\n내일 신관 밥 뭐나와?'
			})

	except Exception as e:
		print(f"cjfreshmeal error: {str(e)}")
		return _errorResponse(quickReplies, '죄송합니다.\n프레시밀 서버연결이 원활하지 않습니다. (흑흑)')

	if imgYN:
		for i in range(len(items)):
			if 'thumbnail' not in items[i]:
				items[i]['thumbnail'] = {'imageUrl': 'https://johun204.github.io/kbsigi/image/no_image.png'}
			items[i]['description'] = items[i]['description'].strip().replace('\n', ', ')
		return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}

	return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'textCard', 'items': items}}], 'quickReplies': quickReplies}}
