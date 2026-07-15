"""
KT희망나눔재단 (카카오톡 플러스친구 게시글 기반) 메뉴 조회 모듈
"""
import requests

from common import cvtDate, normalize_date_string

LOCATION_NM = 'KT희망나눔재단'


def _buildQuickReplies():
	quickReplies = []
	quickReplies.append({'label': 'KT', 'action': 'message', 'messageText': '오늘 ' + LOCATION_NM + ' 메뉴 알려줘~!'})
	quickReplies.append({'label': '전경련', 'action': 'message', 'messageText': '오늘 전경련 메뉴 알려줘~!'})
	quickReplies.append({'label': '처음으로', 'action': 'message', 'messageText': '처음으로'})
	return quickReplies


def getKTmenu(req_dt):
	location_nm = LOCATION_NM
	quickReplies = _buildQuickReplies()

	items = []

	try:
		response = requests.get(
			url='https://pf.kakao.com/rocket-web/web/v2/profiles/_bwyrs',
			headers={'Content-Type': 'application/json'}
		)
		jsondata = response.json()

		posts = [x for x in jsondata["cards"] if x["title"] == "소식"]

		if len(posts) == 0 or "posts" not in posts[0]:
			items.append({
				'title': '오류',
				'description': '죄송합니다.\n식단정보를 불러올 수 없습니다. (흑흑)',
				'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},
				'buttons': [{'action': 'webLink', 'label': 'KT 플러스친구', 'webLinkUrl': 'https://pf.kakao.com/_bwyrs/posts'}]
			})
			return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}

		weekly = None
		for x in posts[0]["posts"]:
			if "주간식단표" in x["title"] and "media" in x and len(x["media"]) > 0 and "url" in x["media"][0]:
				weekly = {"title": x["title"], "image": x["media"][0]["url"]}

			if "title" in x and req_dt == normalize_date_string(x["title"]) and "contents" in x and len(x["contents"]) > 0 and "v" in x["contents"][0]:
				img_url = "https://johun204.github.io/kbsigi/image/no_image.png"
				if "media" in x and len(x["media"]) > 0 and "url" in x["media"][0]:
					img_url = x["media"][0]["url"]
				items.append({
					'title': x["title"] + ' - ' + location_nm,
					'description': x["contents"][0]["v"],
					'thumbnail': {'imageUrl': img_url},
					'buttons': [{'action': 'webLink', 'label': '사진 크게보기', 'webLinkUrl': img_url}]
				})

		if len(items) == 0:
			if weekly:
				items.append({
					'title': weekly["title"],
					'description': weekly["title"],
					'thumbnail': {'imageUrl': weekly["image"]},
					'buttons': [{'action': 'webLink', 'label': '사진 크게보기', 'webLinkUrl': weekly["image"]}]
				})
			items.append({
				'title': cvtDate(req_dt) + ' ' + location_nm,
				'description': '등록된 식단정보가 없습니다.\n잠시후 다시 시도해주세요 (흑흑)',
				'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},
				'buttons': [{'action': 'webLink', 'label': 'KT 플러스친구', 'webLinkUrl': 'https://pf.kakao.com/_bwyrs/posts'}]
			})
			return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}

		if weekly:
			items.append({
				'title': weekly["title"],
				'description': weekly["title"],
				'thumbnail': {'imageUrl': weekly["image"]},
				'buttons': [{'action': 'webLink', 'label': '사진 크게보기', 'webLinkUrl': weekly["image"]}]
			})

	except Exception as e:
		print(f"KT error: {str(e)}")
		items.append({
			'title': '오류',
			'description': '죄송합니다.\nKT 카톡플러스친구 서버연결이 원활하지 않습니다. (흑흑)',
			'thumbnail': {'imageUrl': 'https://johun204.github.io/kbsigi/image/error.png'},
			'buttons': [{'action': 'webLink', 'label': 'KT 플러스친구', 'webLinkUrl': 'https://pf.kakao.com/_bwyrs/posts'}]
		})
		return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}

	return {'version': '2.0', 'template': {'outputs': [{'carousel': {'type': 'basicCard', 'items': items}}], 'quickReplies': quickReplies}}
