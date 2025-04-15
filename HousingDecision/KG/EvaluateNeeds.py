# Editor:CharPy
import numpy as np

from GoodTools import *
from py2neo import Graph
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)

class NeedsEvaluator:
	def __init__(self, tool, chart = None):
		self.cypher_tail = ("WITH h, \n" +
							"\tCOUNT(CASE f.facility_type WHEN '教育' THEN 1 ELSE NULL END) AS educationCount,\n" +
							"\tCOUNT(CASE f.facility_type WHEN '交通' THEN 1 ELSE NULL END) AS transportCount,\n" +
							"\tCOUNT(CASE f.facility_type WHEN '医疗' THEN 1 ELSE NULL END) AS medicalCount,\n" +
							"\tCOUNT(CASE f.facility_type WHEN '商业' THEN 1 ELSE NULL END) AS businessCount\n" +
							"MATCH (r:Region {region_id: LEFT(h.house_id, 6)})\n" +
							"\tWITH DISTINCT h, r, educationCount, transportCount, medicalCount, businessCount\n"
							"\tRETURN h.house_name AS houseName, \n" +
							"\th.house_address AS houseAddress, \n" +
							"\th.average_price AS averagePrice, \n" +
							"\th.floor_plan AS floorPlan, \n" +
							"\th.floor_size AS floorSize, \n" +
							"\th.house_link AS houseLink, \n" +
							"\tLEFT(h.house_id, 2) AS cityID, \n" +
							"\tLEFT(h.house_id, 4) AS districtID, \n" +
							"\tr.region_name AS regionName, \n" +
							"\teducationCount AS eduCount, \n" +
							"\ttransportCount AS trsCount, \n" +
							"\tmedicalCount AS medCount, \n" +
							"\tbusinessCount AS bizCount")
		self.tool = tool
		self.g = Graph("http://localhost:7474", auth = ("neo4j", "Pine20210238"))

		self.RI = {3: 0.58, 4: 0.89, 5: 1.12, 6: 1.26, 7: 1.36, 8: 1.41, 9: 1.46, 10: 1.49, 11: 1.52, 12: 1.54, 13: 1.56, 14: 1.58}

		if chart is None:
			self.chart = {'budget': dict(), 'size': dict(), 'facility': dict(),  # 数字筛选条件（预算范围、面积范围、配套组合）
						  'region': dict(), 'plan': dict(), 'developer': dict()}  # 文字筛选条件（对地区、户型、开发商的要求）

		self.self_weight = dict()  # 用户自行输入的权重

		self.less_rate = {0: 0.3, 2: 0.25, 4: 0.2, 6: 0.15,
						  8: 0.1}  # 当用户没有设置预算下限时，根据用户设置的预算上限所处区间计算下限的系数a，即下限 = 上限 * (1 - a)

		self.detail_chart = {'bgt_upper': 'budget', 'bgt_lower': 'budget',
							 'size_upper': 'size', 'size_lower': 'size',
							 'vital_facility': 'facility', 'if_location': 'region',
							 'if_plan': 'plan', 'if_developer': 'developer'}

		self.empty_detail = ['bgt_upper', 'bgt_lower', 'size_upper', 'size_lower',
							 'vital_facility', 'if_location', 'if_plan', 'if_developer']

		self.main_info = {
			'start_info': "您已进入房源评估程序，您需要尽可能按照所给出的规范填写数据，否则评估过程可能中断甚至失败",
			"gather_info": "您接下来需要根据我给出的提示输入采集信息",
			"fix_info": "您的输入数据有所缺漏，请按照提示补充完整",
			"eval_info": "您的数据已输入完毕，正在为您初步筛选房源......"}

		self.detail_info = {'bgt_upper': "#请输入一个整数表示您的房款预算上限（单位：元）：",
							'bgt_lower': "#请输入一个整数表示您的房款预算下限，您也可以跳过不填写（单位：元）：",
							'size_upper': "#请输入一个整数表示购房面积上限（单位：平方米）：",
							'size_lower': "#请输入一个整数表示购房面积下限（单位：平方米）：",
							'vital_facility': "#请在（商业、医疗、交通、教育）中选择您希望重点考虑的配套类型，请用空格间隔输入" + \
											  "（如果您不需要重点考虑任何一类则可以跳过不填写）：",
							'if_location': "#如果您只考虑个别城市/市辖区/市内地区，请用空格间隔输入其名称，您也可以跳过不填写：",
							'if_plan': "#如果您只考虑个别户型，请用空格间隔输入整数a，您也可以跳过不填写（a表示您考虑a室的户型）：",
							'if_developer': "#如果您只考虑个别开发商，请用空格间隔输入其名称，您也可以跳过不填写："}

		self.confirm_info = {'bgt_upper': "#未能检测到有效的房款预算上限，需要重新输入",
							 'bgt_lower': "#未能检测到有效的房款预算下限，您是否需要重新输入(y/n)：",
							 'size_upper': "#未能检测到有效的面积上限，需要重新输入",
							 'size_lower': "#未能检测到有效的面积下限，需要重新输入",
							 'vital_facility': "#未能检测到有效的配套筛选信息，您是否需要重新输入(y/n)：",
							 'if_location': "#未能检测到有效的地区筛选信息，您是否需要重新输入(y/n)：",
							 'if_plan': "#未能检测到有效的户型筛选信息，您是否需要重新输入(y/n)：",
							 'if_developer': "#未能检测到有效的开发商筛选信息，您是否需要重新输入(y/n)："}

		self.singleHouseTemplate = "\n##楼盘 {0}：\n**地址：{1} {2} {3} {4}\n**户型：{5}\n**面积：{6}-{7}㎡" + \
								   "\n**均价：{8}元/m²\n**平均总房款：{9}-{10}元\n**更多详情：{11}元\n-------------------------"
		self.completeHouseTemplate = "\n房源评估分数：{12}\n##楼盘 {0}：\n**地址：{1} {2} {3} {4}\n**户型：{5}\n**面积：{6}-{7}㎡" + \
			                 "\n**均价：{8}元/m²\n**平均总房款：{9}-{10}元\n**更多详情：{11}\n-------------------------"

	def beautify_frame(self, vf):
		sentence = ""
		for i in range(len(vf)):
			# 户型信息排版（如果有）
			floorPlanInfo = ""
			floorPlanTemplate = "{0}室/"
			for elem in eval(vf['floorPlan'][i]):
				if eval(elem) > 0:
					floorPlanInfo += floorPlanTemplate.format(elem)

			if 'rank' in vf.columns:
				sentence += self.completeHouseTemplate.format(vf["houseName"][i],
															self.tool.use_locDictReverse()[vf["cityID"][i]],
															self.tool.use_locDictReverse()[vf["districtID"][i]],
															vf["regionName"][i], vf["houseAddress"][i],
															floorPlanInfo, vf["sizeLower"][i],
															vf["sizeUpper"][i], vf["averagePrice"][i],
															vf["priceLower"][i], vf["priceUpper"][i],
															vf["houseLink"][i], vf["rank"][i])

			else:
				sentence += self.singleHouseTemplate.format(vf["houseName"][i],
															self.tool.use_locDictReverse()[vf["cityID"][i]],
															self.tool.use_locDictReverse()[vf["districtID"][i]],
															vf["regionName"], vf["houseAddress"][i],
															floorPlanInfo, vf["sizeLower"][i],
															vf["sizeUpper"][i], vf["averagePrice"][i],
															vf["priceLower"][i], vf["priceUpper"][i],
															vf["houseLink"][i])
		return sentence

	def evaluator_main(self):
		self.tool.print_prefix(self.main_info["start_info"])

		# 采集信息
		need = self.gather_weights(self.empty_detail)
		while need:
			need = self.gather_weights(need)

		# self.chart = {'budget': {'bgt_upper': 7800000, 'bgt_lower': 5600000},
		# 			  'size': {'size_upper': 110, 'size_lower': 90},
		# 			  'facility': {'vital_facility': {'商业': 0.1, '教育': 0.1, '交通': 0.4, '医疗': 0.2}},
		# 			  'region': {'if_location': {'广州', '南山'}},
		# 			  'plan': {'if_plan': {2, 3}},
		# 			  'developer': {'if_developer': {'越秀'}}}

		# 采集完毕，根据户型、开发商、地点、配套进行初步筛选，如果这部分筛选结果为空则直接结束
		self.tool.print_prefix(self.main_info["eval_info"])
		query = ["MATCH (h:House)-[n:H_NEAR_F]->(f:Facility)"]
		for crt in ['if_plan', 'if_developer', 'if_location', 'vital_facility']:
			query.extend(self.evaluation_parser(crt))

		query.append(self.cypher_tail)
		first_query = "\n".join(query)

		# 初步筛选完毕，若没有结果就直接结束
		first_round = self.g.run(first_query).data()
		if len(first_round) == 0:
			return "抱歉，根据您的筛选条件，没有找到合适的房源，请回到聊天模式重新提问"

		# 结果不为空，根据预算、面积进行进一步筛选
		stage_frame = {'houseName': [], 'houseAddress': [], 'averagePrice': [], 'floorPlan': [],
					   'floorSize': [], 'houseLink': [], 'cityID': [], 'districtID': [],
					   'regionName': [], 'eduCount': [], 'trsCount': [], 'medCount': [], 'bizCount': []}
		for item in first_round:
			for key in stage_frame.keys():
				stage_frame[key].append(item[key])

		deep_frame = pd.DataFrame(stage_frame)
		verified_frame = self.verify_data(deep_frame)
		if len(verified_frame) == 0:
			return "抱歉，在该查询条件下所得房源信息尚不完善，请回到聊天模式继续提问"
		elif len(verified_frame) == 1:
			eval_result = "根据您的筛选条件，我为您唯一一套信息完整的房源，请您过目："
			eval_result += self.beautify_frame(verified_frame)
			return eval_result
		else:  # 基于层次分析法计算权重和
			eval_result = "根据您的筛选条件，我为您筛选出一部分信息完整的房源，请您过目："
			sizeMatrix = self.generate_matrix(verified_frame['averageSize'])
			priceMatrix = self.generate_matrix(verified_frame['averageTotal'])
			facMatrix = self.generate_matrix(verified_frame["facCount"])
			matrix_dict = {'size': sizeMatrix, 'price': priceMatrix, 'fac': facMatrix}
			vec_dict = dict()

			for key in matrix_dict.keys():
				validity = self.matrix_validity(matrix_dict[key])
				vec_dict[key] = validity['vec']
				if validity['CI'] < 0.1 and validity['CR'] < 0.1:
					self.tool.print_prefix("数据矩阵{}已经过验证".format(key))

			self.final_weight()
			r_list = []
			for i in range(len(verified_frame)):
				plus = 0
				for key in vec_dict.keys():
					plus += self.self_weight[key] * vec_dict[key][i]
				r_list.append(plus)
			vec_dict['rank'] = r_list
			verified_frame = pd.concat([verified_frame, pd.DataFrame(vec_dict)], axis=1)

			verified_frame = verified_frame.sort_values(by=["rank"], ascending=False)
			eval_result += self.beautify_frame(verified_frame)
			return eval_result

	def verify_data(self, deep_frame):
		deep_frame["floorSize"] = deep_frame["floorSize"].apply(lambda x: x[1:len(x)-1].split(", "))
		deep_frame["sizeUpper"] = deep_frame["floorSize"].apply(lambda x: int(x[1].replace("'", "")))
		deep_frame["sizeLower"] = deep_frame["floorSize"].apply(lambda x: int(x[0].replace("'", "")))
		deep_frame["averageSize"] = deep_frame["floorSize"].apply(
			lambda x: int((int(x[0].replace("'", "")) + int(x[1].replace("'", ""))) / 2))

		deep_frame = deep_frame[deep_frame["averageSize"] != 0]  # 去除0面积房源
		deep_frame = deep_frame[deep_frame["averagePrice"] != 0]  # 去除0均价房源

		deep_frame["priceUpper"] = deep_frame["averagePrice"] * deep_frame["sizeUpper"]
		deep_frame["priceLower"] = deep_frame["averagePrice"] * deep_frame["sizeLower"]
		deep_frame["averageTotal"] = deep_frame["averagePrice"] * deep_frame["averageSize"]
		# 把房源上限不足期望下限的行去掉
		deep_frame = deep_frame[self.chart['size']['size_lower'] < deep_frame["sizeUpper"]]
		# 房源下限超过预算上限的行去掉
		deep_frame = deep_frame[self.chart['budget']['bgt_upper'] > deep_frame["priceLower"]]

		if len(deep_frame):
			# 计算面积区间重合度
			upper_bound = np.minimum(self.chart['size']['size_upper'], deep_frame["sizeUpper"])
			lower_bound = np.maximum(self.chart['size']['size_lower'], deep_frame["sizeLower"])
			# 计算交叉长度并确保非负
			deep_frame["sizeCross"] = (upper_bound - lower_bound).clip(lower = 0)
			if deep_frame["sizeCross"].value_counts().idxmax() == 0:
				self.tool.print_prefix("您的期望面积上限不足这批房源的下限，意味着您有机会购买到更大面积的房源，我已重设了您的期望面积区间")
				self.chart['size']['size_upper'] = deep_frame["sizeUpper"].max()
				self.chart['size']['size_lower'] = deep_frame["sizeLower"].min()

			upper_bound = np.minimum(self.chart['budget']['bgt_upper'], deep_frame["priceUpper"])
			lower_bound = np.maximum(self.chart['budget']['bgt_lower'], deep_frame["priceLower"])
			# 计算交叉长度并确保非负
			deep_frame["priceCross"] = (upper_bound - lower_bound).clip(lower = 0)
			if deep_frame["priceCross"].value_counts().idxmax() == 0:
				self.tool.print_prefix("您的预算下限超过了这批房源的上限，意味着您预算充足，我已重设了您的预算区间")
				self.chart['budget']['bgt_upper'] = deep_frame["priceUpper"].max()
				self.chart['budget']['bgt_lower'] = deep_frame["priceLower"].min()

			# 按照所输入的重点考虑配套类型权重进行加权求和
			deep_frame["facCount"] = (
					self.chart['facility']['vital_facility']["教育"] * deep_frame["eduCount"] +
					self.chart['facility']['vital_facility']["交通"] * deep_frame["trsCount"] +
					self.chart['facility']['vital_facility']["医疗"] * deep_frame["medCount"] +
					self.chart['facility']['vital_facility']["商业"] * deep_frame["bizCount"]
			).round().astype(int)

			# 根据加权配套数排序
			deep_frame = deep_frame.sort_values(by="facCount", ascending=False)

		return deep_frame.head(14)

	def generate_matrix(self, numbers):
		n = len(numbers)
		matrix = [[0.0] * n for _ in range(n)]

		for i in range(n):
			for j in range(n):
				if i == j:
					matrix[i][j] = 1.0  # 对角线元素为1
				else:
					matrix[i][j] = numbers[i] / numbers[j]
		return matrix

	def matrix_validity(self, matrix):
		n = len(matrix)
		# 列归一化
		for j in range(n):
			# 求列和
			column_sum = 0
			for i in range(n):
				column_sum += matrix[i][j]
			# 列元素除以列和
			for i in range(n):
				matrix[i][j] /= column_sum
		# 求行和
		vec = [sum(matrix[k]) for k in range(n)]
		# 行归一化
		for i in range(n):
			vec[i] /= sum(vec)
		# 利用归一化权重vec求特征向量
		for i in range(n):
			for j in range(n):
				matrix[i][j] *= vec[j]
		ftr = [sum(matrix[k]) for k in range(n)]

		# 求最大特征根
		max_lambda = sum([ftr[k] / (n*vec[k]) for k in range(n)])

		# 判断矩阵的一致性指标CI
		CI = (max_lambda - n) / (n - 1)
		RI = self.RI[n]
		CR = CI / RI

		return {'vec': vec, 'CI': CI, 'CR': CR}
		# 判断矩阵的一致性比例CR

	def final_weight(self):
		self.tool.print_prefix("接下来请你为下列的筛选条件设置权重，请输入1到10之间的整数，权重越高表示您越重视该条件：")

		pw = abs(int(input("价格重要性：")))
		sw = abs(int(input("面积重要性：")))
		fw = abs(int(input("配套重要性：")))
		tw = (pw + sw + fw) / 30

		pw = 1 if pw <= 0 or pw > 10 else pw
		sw = 1 if sw <= 0 or sw > 10 else sw
		fw = 1 if fw <= 0 or fw > 10 else fw
		tw = 3 if tw <= 0 or tw > 30 else tw

		self.self_weight.update({'price': pw / tw})
		self.self_weight.update({'size': sw / tw})
		self.self_weight.update({'fac': fw / tw})

	def gather_weights(self, need_gather):
		self.tool.print_prefix(self.main_info["gather_info"])
		for detail in need_gather:
			self.chart[self.detail_chart[detail]].update({detail: input(self.detail_info[detail])})

		isFixed = []
		for fix in need_gather:
			isFixed.append(self.fix_weights(fix))
		tmpFixed = []
		for i in range(len(need_gather)):
			if not isFixed[i]:
				tmpFixed.append(need_gather[i])
		return tmpFixed

	def fix_weights(self, need_fix):
		fix = need_fix
		if fix == 'bgt_upper':
			wgh = self.chart[self.detail_chart[fix]][fix]
			if not str(wgh).isnumeric():
				self.tool.print_prefix(self.confirm_info[fix])
			else:
				self.chart[self.detail_chart[fix]][fix] = int(wgh)
				return True

		elif fix == 'size_upper':
			wgh = self.chart[self.detail_chart[fix]][fix]
			if not str(wgh).isnumeric():
				self.tool.print_prefix(self.confirm_info[fix])
			else:
				self.chart[self.detail_chart[fix]][fix] = int(wgh)
				return True

		elif fix == 'size_lower':
			wgh = self.chart[self.detail_chart[fix]][fix]
			if not str(wgh).isnumeric():
				self.tool.print_prefix(self.confirm_info[fix])
			else:
				self.chart[self.detail_chart[fix]][fix] = int(wgh)
				return True

		elif fix == 'bgt_lower':
			wgh = self.chart[self.detail_chart[fix]][fix]
			if not str(wgh).isnumeric():
				checkUpper = self.chart[self.detail_chart[fix]]['bgt_upper']
				if str(checkUpper).isnumeric():
					confirm = input(self.confirm_info[fix])
					if confirm.lower() != 'y':
						firstNum = checkUpper // 1000000
						if firstNum < 8:
							lowerSelect = firstNum if firstNum % 2 == 0 else firstNum - 1
						else:
							lowerSelect = 8
						self.chart[self.detail_chart[fix]][fix] = int(checkUpper * (1 - self.less_rate[lowerSelect]))
						return True
			else:
				self.chart[self.detail_chart[fix]][fix] = int(wgh)
				return True

		elif fix == 'vital_facility':
			yesFac = set(self.chart[self.detail_chart[fix]][fix].split()) & self.tool.use_fac()
			if not yesFac:
				confirm = input(self.confirm_info[fix])
				if confirm.lower() != 'y':
					return True
			else:
				noFac = self.tool.use_fac() - yesFac
				tmp = 1
				self.chart[self.detail_chart[fix]][fix] = dict()
				for fac in noFac:
					self.chart[self.detail_chart[fix]][fix].update({fac: 0.1})
					tmp -= 0.1
				for fac in yesFac:
					share = tmp / len(yesFac)
					self.chart[self.detail_chart[fix]][fix].update({fac: share})
					tmp -= share
				return True

		elif fix == 'if_plan':
			yesPlan = set(self.chart[self.detail_chart[fix]][fix].split())
			tmp = set()
			for num in yesPlan:
				if num.isnumeric():
					tmp.add(int(num))
			if not tmp:
				confirm = input(self.confirm_info[fix])
				if confirm.lower() != 'y':
					return True
			else:
				self.chart[self.detail_chart[fix]][fix] = tmp
				return True

		elif fix == 'if_developer':
			yesDev = set(self.chart[self.detail_chart[fix]][fix].split()) & self.tool.use_dev()
			if not yesDev:
				confirm = input(self.confirm_info[fix])
				if confirm.lower() != 'y':
					return True
			else:
				self.chart[self.detail_chart[fix]][fix] = yesDev
				return True

		elif fix == 'if_location':
			yesLoc = set(self.chart[self.detail_chart[fix]][fix].split()) & self.tool.use_loc()
			if not yesLoc:
				confirm = input(self.confirm_info[fix])
				if confirm.lower() != 'y':
					return True
			else:
				self.chart[self.detail_chart[fix]][fix] = yesLoc
				return True

		return False

	def evaluation_parser(self, crt):
		query = []
		evalList = list(self.chart[self.detail_chart[crt]][crt])
		if evalList:
			if crt == "vital_facility":
				query.append("\tAND f.facility_type IN {0}".replace("{0}", str(evalList)))
			elif crt == "if_plan":
				query.append('''WHERE REPLACE(h.floor_plan, ' ', '') <> "('0','0')"''')
				query.append(
					'''WITH h, f, REPLACE(REPLACE(SUBSTRING(h.floor_plan, 2, SIZE(h.floor_plan)-2), "'", ""), " ", "") AS cleaned''')
				query.append('''WITH h, f, SPLIT(cleaned, ',') AS parts''')
				query.append('''WITH h, f, [p IN parts | TOINTEGER(p)] AS planNumbers''')
				query.append('''WHERE ANY(pl IN planNumbers WHERE pl IN {0})'''.replace('{0}', str(evalList)))
			elif crt == "if_developer":
				query.append('''\tAND ANY(dv IN {0} WHERE h.house_name CONTAINS dv)'''.replace('{0}', str(evalList)))
			elif crt == "if_location":
				queryLoc = []  # 将地点都转换为对应id
				for loc in evalList:
					queryLoc.append(self.tool.use_locDict()[loc])

				query.append('''\tAND ANY(_ IN {0} WHERE h.house_id CONTAINS _)'''.replace('{0}', str(queryLoc)))

		return query


if __name__ == '__main__':

	"""
	7800000
	5600000
	110
	90
	交通 娱乐 医疗
	广州 南山
	2 3
	越秀
	"""

	gt = GoodTools("Prefix:", "Default Message")
	NeedsEvaluator(gt).evaluator_main()
