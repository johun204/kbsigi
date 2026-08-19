import json
import os
from openai import OpenAI
from common import is_error_response, is_no_data_response

def kbsigi_pick_with_ai(menu_json):
	output = {
		"template": {
			"outputs": [],
			"quickReplies": menu_json["template"]["quickReplies"]
		},
		"version": "2.0"
	}
	if is_error_response(menu_json):
		print(f"에러 발생. 잠시후 다시 시도해주세요.")
		output["template"]["outputs"].append({"textCard": {"title":"오류", "description": f"식단정보에 오류가 있습니다.\n잠시후 다시 시도해주세요."}})
		return output

	if is_no_data_response(menu_json):
		print(f"식단을 불러올 수 없습니다. 잠시후 다시 시도해주세요.")
		output["template"]["outputs"].append({"textCard": {"title":"오류", "description": f"등록된 식단정보가 없습니다.\n잠시후 다시 시도해주세요."}})
		return output
	recommend_meal = recommend_menu(menu_json)

	if 'error' in recommend_meal:
		print(f"{recommend_meal['error']}")
		output["template"]["outputs"].append({"textCard": {"title":"오류", "description": f"{recommend_meal['error']}"}})
		return output

	try:
		output_meal = [x for x in menu_json['template']['outputs'][0]['carousel']['items'] if recommend_meal['title'] == x['title']]

		if len(output_meal) == 0:
			print(f"추천 메뉴가 없습니다. {recommend_meal['title']}")
			output["template"]["outputs"].append({"textCard": {"title":"오류", "description": f"추천 메뉴를 고민하고 있습니다.\n잠시후 다시 시도해주세요."}})
			return output
		output_meal[0]["description"] = f"{recommend_meal['reason'].strip()}\n\n※ 위 내용은 생성형 AI를 통해 작성되었습니다."

		if 'thumbnail' in output_meal[0]:
			output["template"]["outputs"].append({"basicCard": output_meal[0]})
		else:
			output["template"]["outputs"].append({"textCard": output_meal[0]})
	except Exception as e:
		print(str(e))
		output["template"]["outputs"].append({"textCard": {"title":"오류", "description": f"API 호출 또는 처리 중 오류가 발생했습니다: {str(e)}.\n잠시후 다시 시도해주세요."}})
		return output

	return output

def recommend_menu(menu_json):
	try:
		menu_outputs = menu_json['template']['outputs'][0]['carousel']

		client = OpenAI(
			base_url="https://integrate.api.nvidia.com/v1",
			api_key=os.environ.get("NVIDIA_API_KEY")
		)

	except Exception as e:
		print(str(e))
		return {"error": f"{str(e)}"}

	prompt = """
	주어진 구내식당 메뉴 데이터에서 점심 식사로 메인 식단 하나를 추천하세요.
	제약 조건:
	1. '샐러드바', '밀박스', '샌드위치' 등 가벼운 식사류는 완전히 제외하고, 정식 메인 메뉴 중에서만 1개를 선택해야 합니다.
	2. 추천 식단의 이름(title), 추천 이유(reason)를 포함해야 합니다.
	3. 추천 식단의 이름(title)은 반드시 주어진 구내식당 메뉴 목록 입력 데이터의 title 중에서 선택하시오. 
	4. 추천 이유(reason)는 제공된 날짜, 칼로리, 영양 성분, 메뉴 구성 등을 바탕으로 두 문장 이내로 한국어로 작성하세요.
	5. 한 문장이 끝나면 개행문자를 포함하고 다음 문장을 작성하세요.
	6. 반드시 제공된 recommend_meal 함수를 호출하여 결과를 전달해야 합니다.
	"""

	tools = [{
		"type": "function",
		"function": {
			"name": "recommend_meal",
			"description": "조건에 맞는 메인 식단을 추천하고 추천 이유를 반환합니다.",
			"parameters": {
				"type": "object",
				"properties": {
					"title": {"type": "string"},
					"reason": {"type": "string"}
				},
				"required": ["title", "reason"]
			}
		}
	}]

	try:
		completion = client.chat.completions.create(
			model="openai/gpt-oss-20b",
			messages=[
				{"role": "system", "content": prompt},
				{"role": "user", "content": json.dumps(menu_outputs, ensure_ascii=False)}
			],
			tools=tools,
			tool_choice={"type": "function", "function": {"name": "recommend_meal"}},
			temperature=1,
			top_p=1,
			max_tokens=4096,
			stream=False
		)

		if not completion.choices or not completion.choices[0].message.tool_calls:
			return {"error": "추천 메뉴 선택에 문제가 발생했습니다.\n잠시후 다시 시도해주세요."}

		tool_call = completion.choices[0].message.tool_calls[0]
		return json.loads(tool_call.function.arguments)

	except json.JSONDecodeError:
		return {"error": "추천 메뉴 정보를 JSON으로 변환하는 데 실패했습니다.\n잠시후 다시 시도해주세요."}
	except Exception as e:
		return {"error": f"API 호출 또는 처리 중 오류가 발생했습니다: {str(e)}.\n잠시후 다시 시도해주세요."}
