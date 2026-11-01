"""
현대그린푸드 H Cafeteria (여의도IT센터) 메뉴 조회 모듈
"""
import json
import os

import requests

from common import cvtDate

HCAFETERIA_KEY = os.getenv('HCAFETERIA_KEY')
HCAFETERIA_URL = os.getenv('HCAFETERIA_URL')

LOCATION_NM = '여의도IT센터'


def _getHcookie():
	dict_data = HCAFETERIA_KEY
	response = requests.post(
		url='https://hcafe.hgreenfood.com/api/com/login.do',
		data=dict_data,
		headers={'Content-Type': 'application/json'}
	)
	jsondata = response.headers['Set-Cookie']
	jsondata = 'MBLCTF_SESSIONID_PRD=' + jsondata.split('MBLCTF_SESSIONID_PRD=')[1].split(';')[0]
	return jsondata


def _buildQuickReplies(location_nm):
	quickReplies = []
	quickReplies.append({'label': '오늘', 'action': 'message', 'messageText': f'오늘 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label': '내일', 'action': 'message', 'messageText': f'내일 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label': '모레', 'action': 'message', 'messageText': f'모레 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label': '처음으로', 'action': 'message', 'messageText': '처음으로'})
	return quickReplies


def _errorResponse(quickReplies, message):
	items = [{
		'title': '오류',
		'description': message,
		'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},
		'buttons': [
			{'action': 'webLink', 'label': 'Android 앱 설치', 'webLinkUrl': 'https://play.google.com/store/apps/details?id=com.ehyundai.greenfood'},
			{'action': 'webLink', 'label': 'iOS 앱 설치', 'webLinkUrl': 'https://apps.apple.com/kr/app/h-cafeteria/id1316351839?l=en'},
		]
	}]
	return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}


def getHmenu(req_dt, bizplc_cd='173148'):
	location_nm = LOCATION_NM
	quickReplies = _buildQuickReplies(location_nm)

	items = []
	imgYN = False
	dict_data = {'prvdDt': req_dt, 'bizplcCd': bizplc_cd}

	try:
		response = requests.post(
			url=HCAFETERIA_URL,
			data=json.dumps(dict_data),
			headers={'Content-Type': 'application/json', 'Cookie': _getHcookie()}
		)
		jsondata = response.json()
	except Exception as e:
		print(f"hcafeteria error: {str(e)}")
		return _errorResponse(quickReplies, '죄송합니다.\n현대그린푸드 서버연결이 원활하지 않습니다. (흑흑)')

	if not jsondata['errorCode'] == 0:
		return _errorResponse(quickReplies, '죄송합니다.\n식단정보를 불러올 수 없습니다. (흑흑)')

	todayList = jsondata['dataSets']['menuList']
	for menu in todayList:
		if menu['prvdDt'] == req_dt:
			if menu['mnuNms'] == "":
				continue
			if menu['dispNm'] != "":
				menu['mnuNms'] = menu['mnuNms'].replace(menu['dispNm'], menu['dispNm'] + ' ✓')
			desc_txt = menu['mnuNms'].replace(', ', '\n')

			totCaloryQt = ''
			if 'totCaloryQt' in menu:
				try:
					totCaloryQt = ' (' + str(int(menu['totCaloryQt'])) + ' kcal)'
				except Exception:
					pass
			if ('imgPath' in menu) and menu['imgPath'] == "":
				items.append({
					'title': cvtDate(menu['prvdDt']) + ' ' + location_nm + ' - ' + menu['conerNm'] + totCaloryQt,
					'description': desc_txt
				})
			else:
				items.append({
					'title': cvtDate(menu['prvdDt']) + ' ' + location_nm + ' - ' + menu['conerNm'] + totCaloryQt,
					'description': desc_txt,
					'thumbnail': {'imageUrl': 'https://hcafe.hgreenfood.com' + menu['imgPath']},
					'buttons': [{'action': 'webLink', 'label': '사진 크게보기', 'webLinkUrl': 'https://hcafe.hgreenfood.com' + menu['imgPath']}]
				})
				imgYN = True

	if len(items) == 0:
		items.append({
			'title': cvtDate(req_dt) + ' ' + location_nm,
			'description': '등록된 식단정보가 없습니다.\n다른 날짜로 다시 물어봐주세요 (흑흑)',
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
