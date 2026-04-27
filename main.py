import requests
import json
import os
from datetime import date, timedelta, datetime, timezone
import time
import re

HCAFETERIA_KEY = os.getenv('HCAFETERIA_KEY')
OURHOME_KEY = os.getenv('OURHOME_KEY')

HCAFETERIA_URL = os.getenv('HCAFETERIA_URL')
OURHOME_URL = os.getenv('OURHOME_URL')
CJFRESH_URL = os.getenv('CJFRESH_URL')

def getWeather():
	temp = ''
	try:
		response = requests.request('GET', 'https://www.kr-weathernews.com/mv3/if/today.fcgi', params={'region':'1156011000'}, timeout=5)
		jsondata = response.json()
		weather = jsondata['current']['wx']

		w=[['☀', '100', '104', '105'], ['☁', '200'], ['⛅', '101', '201'], ['🌧', '102', '103', '202', '203', '300', '301', '302', '303', '304'], ['🌨', '204', '205']]
		for ww in w:
			for i in range(1, len(ww)):
				weather = weather.replace(ww[i], ww[0])
				if len(weather) == 1: break
			if len(weather) == 1: break

		if len(weather) > 1: weather = ''
		hour_num = int((datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%H"))
		temp = f'{("오전" if hour_num < 12 else "오후")} {(hour_num - 1) % 12 + 1}시 여의도 날씨는 {weather} {jsondata["current"]["temp"]}°C 입니다~'
	except:pass
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

def getHcookie():
	dict_data = HCAFETERIA_KEY
	response = requests.post(url='https://hcafe.hgreenfood.com/api/com/login.do', data=dict_data, headers={'Content-Type': 'application/json'})
	jsondata = response.headers['Set-Cookie']
	jsondata = 'MBLCTF_SESSIONID_PRD=' + jsondata.split('MBLCTF_SESSIONID_PRD=')[1].split(';')[0]
	return jsondata

def getHmenu(req_dt, bizplc_cd='173148'):
	location_nm = '여의도IT센터'

	quickReplies = []
	quickReplies.append({'label':'오늘', 'action':'message', 'messageText':f'오늘 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label':'내일', 'action':'message', 'messageText':f'내일 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label':'모레', 'action':'message', 'messageText':f'모레 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label':'처음으로', 'action':'message', 'messageText':'처음으로'})

	items = []
	imgYN = False
	dict_data = {'prvdDt':req_dt, 'bizplcCd':bizplc_cd}

	try:
		response = requests.post(url=HCAFETERIA_URL, data=json.dumps(dict_data), headers={'Content-Type': 'application/json', 'Cookie':getHcookie()})
		jsondata = response.json()
	except Exception as e:
		print(f"hcafeteria error: {str(e)}")
		items.append({'title':'오류','description':'죄송합니다.\n현대그린푸드 서버연결이 원활하지 않습니다. (흑흑)','thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},'buttons': [{'action': 'webLink','label': 'Android 앱 설치','webLinkUrl': 'https://play.google.com/store/apps/details?id=com.ehyundai.greenfood'},{'action': 'webLink','label': 'iOS 앱 설치','webLinkUrl': 'https://apps.apple.com/kr/app/h-cafeteria/id1316351839?l=en'}]})
		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}

	if not jsondata['errorCode'] == 0:
		items.append({'title':'오류','description':'죄송합니다.\n식단정보를 불러올 수 없습니다. (흑흑)','thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},'buttons': [{'action': 'webLink','label': 'Android 앱 설치','webLinkUrl': 'https://play.google.com/store/apps/details?id=com.ehyundai.greenfood'},{'action': 'webLink','label': 'iOS 앱 설치','webLinkUrl': 'https://apps.apple.com/kr/app/h-cafeteria/id1316351839?l=en'}]})
		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}

	todayList = jsondata['dataSets']['menuList']
	for menu in todayList:			
		if menu['prvdDt'] == req_dt:
			if menu['mnuNms'] == "": continue
			if menu['dispNm'] != "": menu['mnuNms'] = menu['mnuNms'].replace(menu['dispNm'], menu['dispNm'] + ' ✓')
			desc_txt = menu['mnuNms'].replace(', ','\n')

			totCaloryQt =  ''
			if 'totCaloryQt' in menu:
				try: totCaloryQt = ' (' + str(int(menu['totCaloryQt'])) + ' kcal)'
				except: pass
			if ('imgPath' in menu) and menu['imgPath'] == "":
				items.append({'title': cvtDate(menu['prvdDt']) + ' ' + location_nm + ' - ' + menu['conerNm'] + totCaloryQt, 'description':desc_txt})
			else:
				items.append({'title': cvtDate(menu['prvdDt']) + ' ' + location_nm + ' - ' + menu['conerNm'] + totCaloryQt, 'description':desc_txt, 'thumbnail': {'imageUrl': 'https://hcafe.hgreenfood.com' + menu['imgPath']} ,'buttons': [{'action': 'webLink','label': '사진 크게보기','webLinkUrl': 'https://hcafe.hgreenfood.com' + menu['imgPath']}]})
				imgYN = True

	if len(items) == 0:
		items.append({'title': cvtDate(req_dt) + ' ' + location_nm,'description': '등록된 식단정보가 없습니다.\n다른 날짜로 다시 물어봐주세요 (흑흑)', 'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'}})
		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}

	if imgYN:
		for i in range(len(items)):
			if 'thumbnail' not in items[i]:
				items[i]['thumbnail'] = {'imageUrl': 'https://johun204.github.io/kbsigi/image/no_image.png'}
			items[i]['description'] = items[i]['description'].strip().replace('\n',',').replace(' ✓','')


	if imgYN:
		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}
	return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'textCard', 'items':items }}], 'quickReplies':quickReplies}}




def getOmenu(req_dt, BUSIPLCD='FA1MO'):
	if BUSIPLCD == 'FA1MO':
		location_nm = '국민은행 신관'
	elif BUSIPLCD == 'FAP56':
		location_nm = '국민은행 본점'

	quickReplies = []
	quickReplies.append({'label':'오늘', 'action':'message', 'messageText':f'오늘 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label':'내일', 'action':'message', 'messageText':f'내일 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label':'모레', 'action':'message', 'messageText':f'모레 {location_nm} 메뉴 알려줘~!'})
	quickReplies.append({'label':'처음으로', 'action':'message', 'messageText':'처음으로'})

	if BUSIPLCD == 'FA1MO':
		quickReplies.append({'label':'오늘 본점', 'action':'message', 'messageText':'오늘 국민은행 본점 메뉴 알려줘~!'})
	elif BUSIPLCD == 'FAP56':
		quickReplies.append({'label':'오늘 신관', 'action':'message', 'messageText':'오늘 국민은행 신관 메뉴 알려줘~!'})

	items = []
	dict = {}
	imgYN = False

	try:
		data = json.loads(OURHOME_KEY)
		data['REQ_PARAMS']['BUSIPLCD'] = BUSIPLCD
		data['REQ_PARAMS']['MENU_DT'] = req_dt

		response = requests.request('POST', OURHOME_URL, data=json.dumps(data), timeout=5)
		jsondata = response.json()

		data = jsondata['returnList']
		for menu in data:
			if not menu['MEALCLASS_CD'] == '2': continue
			for corner in menu['CORNER_INFO']:
				KCAL =  ''
				if 'KCAL' in corner:
					KCAL = ' (' + corner['KCAL'] + ' kcal)'
				desc_txt = corner['MENU_KOR'] + ' ✓\n' + corner['MENU_DTL_KOR'].replace(', ',',').replace(' ,',',').replace(',','\n')
				if corner['MENU_IMG_NM'].find('http') > -1:
					items.append({'title': cvtDate(menu['MENU_DT']) + ' ' + location_nm + ' - ' + corner['CORNER_NM'] + KCAL, 'description':desc_txt, 'thumbnail': {'imageUrl': corner['MENU_IMG_NM']},'buttons': [{'action': 'webLink','label': '사진 크게보기','webLinkUrl': corner['MENU_IMG_NM']}]})
					imgYN = True
				else:
					items.append({'title': cvtDate(menu['MENU_DT']) + ' ' + location_nm + ' - ' + corner['CORNER_NM'] + KCAL, 'description':desc_txt})

	except Exception as e:
		print(f"ourhome error: {str(e)}")
		items = []
		items.append({'title':'오류','description':'죄송합니다.\n아워홈 서버연결이 원활하지 않습니다. (흑흑)', 'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'}, 'buttons': [{'action': 'webLink','label': 'Android 앱 설치','webLinkUrl': 'https://play.google.com/store/apps/details?id=com.ourhome.fsmobileticket'},{'action': 'webLink','label': 'iOS 앱 설치','webLinkUrl': 'https://apps.apple.com/kr/app/meal-care/id1182175084'}]})
		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}

	if len(items) == 0:
		desc_txt = '등록된 식단정보가 없습니다.\n다른 날짜로 다시 물어봐주세요 (흑흑)'
		items.append({'title': cvtDate(req_dt) + ' ' + location_nm, 'description':desc_txt, 'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'}})

		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}
	if imgYN:
		for i in range(len(items)):
			if 'thumbnail' not in items[i]:
				items[i]['thumbnail'] = {'imageUrl': 'https://johun204.github.io/kbsigi/image/no_image.png'}
			items[i]['description'] = items[i]['description'].strip().replace('\n',',').replace(' ✓','')

	if imgYN:
		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}
	return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'textCard', 'items':items }}], 'quickReplies':quickReplies}}


def getKTmenu(req_dt):
	location_nm = 'KT희망나눔재단'

	# quickReplies
	quickReplies = []
	quickReplies.append({'label':'KT', 'action':'message', 'messageText':'오늘 ' + location_nm + ' 메뉴 알려줘~!'})
	quickReplies.append({'label':'전경련', 'action':'message', 'messageText':'오늘 전경련 메뉴 알려줘~!'})
	quickReplies.append({'label':'처음으로', 'action':'message', 'messageText':'처음으로'})

	items = []

	try:
		response = requests.get(url='https://pf.kakao.com/rocket-web/web/v2/profiles/_bwyrs', headers={'Content-Type': 'application/json'})
		jsondata = response.json()
		
		posts = [x for x in jsondata["cards"] if x["title"] == "소식"]

		if len(posts) == 0 or "posts" not in posts[0]:
			items.append({'title':'오류','description':'죄송합니다.\n식단정보를 불러올 수 없습니다. (흑흑)','thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},'buttons': [{'action': 'webLink','label': 'KT 플러스친구','webLinkUrl': 'https://pf.kakao.com/_bwyrs/posts'}]})
			return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}

		weekly = None
		for x in posts[0]["posts"]:
			if "주간식단표" in x["title"] and "media" in x and len(x["media"]) > 0 and "url" in x["media"][0]:
				weekly = {"title": x["title"], "image": x["media"][0]["url"]}

			if "title" in x and req_dt == normalize_date_string(x["title"]) and "contents" in x and len(x["contents"]) > 0 and "v" in x["contents"][0]:
				img_url = "https://johun204.github.io/kbsigi/image/no_image.png"
				if "media" in x and len(x["media"]) > 0 and "url" in x["media"][0]:
					img_url = x["media"][0]["url"]
				items.append({'title': x["title"] + ' - ' + location_nm, 'description':x["contents"][0]["v"], 'thumbnail': {'imageUrl': img_url} ,'buttons': [{'action': 'webLink','label': '사진 크게보기','webLinkUrl': img_url}]})

		if len(items) == 0:
			if weekly:
				items.append({'title': weekly["title"], 'description': weekly["title"], 'thumbnail': {'imageUrl':  weekly["image"]} ,'buttons': [{'action': 'webLink','label': '사진 크게보기','webLinkUrl': weekly["image"]}] })
			items.append({'title': cvtDate(req_dt) + ' ' + location_nm,'description': '등록된 식단정보가 없습니다.\n잠시후 다시 시도해주세요 (흑흑)', 'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},'buttons': [{'action': 'webLink','label': 'KT 플러스친구','webLinkUrl': 'https://pf.kakao.com/_bwyrs/posts'}]})
			return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}

		if weekly:
			items.append({'title': weekly["title"], 'description': weekly["title"], 'thumbnail': {'imageUrl':  weekly["image"]} ,'buttons': [{'action': 'webLink','label': '사진 크게보기','webLinkUrl': weekly["image"]}] })

	except Exception as e:
		print(f"KT error: {str(e)}")
		items.append({'title':'오류','description':'죄송합니다.\nKT 카톡플러스친구 서버연결이 원활하지 않습니다. (흑흑)','thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},'buttons': [{'action': 'webLink','label': 'KT 플러스친구','webLinkUrl': 'https://pf.kakao.com/_bwyrs/posts'}]})
		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}

	return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}



def getFmenu(req_dt, storeIdx, txt):
	if storeIdx == '6083':
		location_nm = '전경련회관'

	dataType, dataName = '2', '중식'
	if txt.find('아침') > -1 or txt.find('조식') > -1:
		dataType, dataName = '1', '조식'
	elif txt.find('점심') > -1 or txt.find('중식') > -1:
		dataType, dataName = '2', '중식'
	elif txt.find('저녁') > -1 or txt.find('석식') > -1:
		dataType, dataName = '3', '석식'

	# quickReplies
	quickReplies = []
	quickReplies.append({'label':'조식', 'action':'message', 'messageText':f'오늘 {location_nm} 조식 메뉴 알려줘~!'})
	quickReplies.append({'label':'중식', 'action':'message', 'messageText':f'오늘 {location_nm} 중식 메뉴 알려줘~!'})	
	quickReplies.append({'label':'석식', 'action':'message', 'messageText':f'오늘 {location_nm} 석식 메뉴 알려줘~!'})
	quickReplies.append({'label':'내일', 'action':'message', 'messageText':f'내일 {location_nm} {dataName} 메뉴 알려줘~!'})
	quickReplies.append({'label':'KT(구내식당)', 'action':'message', 'messageText':'오늘 KT 메뉴 알려줘~!'})
	quickReplies.append({'label':'처음으로', 'action':'message', 'messageText':'처음으로'})

	items = []
	imgYN = False

	try:
		response = requests.request('GET', f'{CJFRESH_URL}?storeIdx={storeIdx}&weekType=1', timeout=10)
		jsondata = response.json()

		if 'data' in jsondata and len(jsondata['data']) > 0:
			for x in jsondata['data']:
				if dataType in jsondata['data'][x] and len(jsondata['data'][x][dataType]) > 0:
					for menu in jsondata['data'][x][dataType]:
						if req_dt == menu['mealDt']:
							if 'thumbnailUrl' in menu and menu['thumbnailUrl'] != "":
								items.append({'title': cvtDate(menu['mealDt']) + ' ' + location_nm + ' - ' + menu['corner'] + '(' + dataName + ')', 'description': menu['name'] + '\n' + ('-' if menu['side'] is None else menu['side']), 'thumbnail': {'imageUrl': menu['thumbnailUrl']},'buttons': [{'action': 'webLink','label': '사진 크게보기','webLinkUrl': menu['thumbnailUrl']}]})
								imgYN = True
							else:
								items.append({'title': cvtDate(menu['mealDt']) + ' ' + location_nm + ' - ' + menu['corner'] + '(' + dataName + ')', 'description': menu['name'] + '\n' + ('-' if menu['side'] is None else menu['side'])})

		if len(items) == 0:
			items.append({'title': cvtDate(req_dt) + ' ' + location_nm + ' - ' + dataName, 'description': '등록된 식단정보가 없습니다.\n다른 날짜로 다시 물어봐주세요 (흑흑)\n\nex) 서관 메뉴 알려줘!\n내일 신관 밥 뭐나와?'})

	except Exception as e:
		print(f"cjfreshmeal error: {str(e)}")
		items = []
		items.append({'title':'오류','description':'죄송합니다.\n프레시밀 서버연결이 원활하지 않습니다. (흑흑)', 'thumbnail':{'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'}, 'buttons': [{'action': 'webLink','label': 'Android 앱 설치','webLinkUrl': 'https://play.google.com/store/apps/details?id=com.cjfreshway.fs.freshmeal'},{'action': 'webLink','label': 'iOS 앱 설치','webLinkUrl': 'https://apps.apple.com/kr/app/id1594764668'}]})
		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}

	if imgYN:
		for i in range(len(items)):
			if 'thumbnail' not in items[i]:
				items[i]['thumbnail'] = {'imageUrl': 'https://johun204.github.io/kbsigi/image/no_image.png'}
			items[i]['description'] = items[i]['description'].strip().replace('\n',', ')

		return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'basicCard', 'items':items }}], 'quickReplies':quickReplies}}
	return {'version': '2.0', 'template': {'outputs': [{'carousel':{ 'type':'textCard', 'items':items }}], 'quickReplies':quickReplies}}


# -------------------- 실행 -------------------- #
if __name__ == "__main__":
	today_date = (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%Y%m%d")
	after1_date = (datetime.now(timezone.utc) + timedelta(hours=9) + timedelta(days=1)).strftime("%Y%m%d")
	after2_date = (datetime.now(timezone.utc) + timedelta(hours=9) + timedelta(days=2)).strftime("%Y%m%d")

	os.makedirs('data', exist_ok=True)

	#default.json
	output = {"template":{"outputs":[{"simpleText":{"text":f"반가워요~!\n{getWeather()}\n어떤곳의 식단을 알려드릴까요? (하하)\n\nex) 서관 메뉴 알려줘!\n내일 신관 밥 뭐나와?"}}], "quickReplies": [ { "label": "전산센터", "action": "message", "messageText": "오늘 여의도전산센터(서관) 메뉴 알려줘~!" }, { "label": "신관", "action": "message", "messageText": "오늘 KB국민은행 신관 메뉴 알려줘~!" }, { "label": "본점", "action": "message", "messageText": "오늘 국민은행 본점 메뉴 알려줘~!" }, { "label": "전경련", "action": "message", "messageText": "오늘 전경련회관 메뉴 알려줘~!" }, { "label": "오늘의 운세", "action": "message", "messageText": "오늘의 운세 알려줘~!" }]},"version":"2.0"}
	with open('data/default.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)

	#hcafeteria.json
	output = getHmenu(today_date, '173148')
	with open('data/hcafeteria.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getHmenu(after1_date, '173148')
	with open('data/hcafeteria_after1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getHmenu(after2_date, '173148')
	with open('data/hcafeteria_after2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)

	#ourhome1.json
	output = getOmenu(today_date, 'FA1MO')
	with open('data/ourhome1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getOmenu(after1_date, 'FA1MO')
	with open('data/ourhome1_after1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getOmenu(after2_date, 'FA1MO')
	with open('data/ourhome1_after2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)

	#ourhome2.json
	output = getOmenu(today_date, 'FAP56')
	with open('data/ourhome2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getOmenu(after1_date, 'FAP56')
	with open('data/ourhome2_after1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getOmenu(after2_date, 'FAP56')
	with open('data/ourhome2_after2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)

	#kt.json
	output = getKTmenu(today_date)
	with open('data/kt.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getKTmenu(after1_date)
	with open('data/kt_after1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getKTmenu(after2_date)
	with open('data/kt_after2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)

	#cjfresh
	output = getFmenu(today_date, '6083', '아침')
	with open('data/cjfresh_1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getFmenu(today_date, '6083', '점심')
	with open('data/cjfresh_2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getFmenu(today_date, '6083', '저녁')
	with open('data/cjfresh_3.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getFmenu(after1_date, '6083', '아침')
	with open('data/cjfresh_1_after1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getFmenu(after1_date, '6083', '점심')
	with open('data/cjfresh_2_after1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getFmenu(after1_date, '6083', '저녁')
	with open('data/cjfresh_3_after1.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getFmenu(after2_date, '6083', '아침')
	with open('data/cjfresh_1_after2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getFmenu(after2_date, '6083', '점심')
	with open('data/cjfresh_2_after2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
	output = getFmenu(after2_date, '6083', '저녁')
	with open('data/cjfresh_3_after2.json', 'w', encoding='utf-8') as f:
		json.dump(output, f, ensure_ascii=False, indent=2)
