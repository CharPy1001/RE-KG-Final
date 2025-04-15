# Editor:CharPy
# Edit time:2025/3/17 18:54
import re
from tabulate import tabulate
from py2neo import Graph
from GoodTools import *


class FigureCaculator:
	def __init__(self, tool):
		self.LPR_list = [0.036, 0.037]  # LPR利率
		self.duration_list = [10, 15, 20, 30]  # 贷款年限
		self.monthly_list = [0.3, 0.35, 0.4]  # 月供占月收入比例
		self.loan_list = [0.7, 0.6, 0.5]  # 贷款比例

		self.tool = tool
		self.locationDictReverse = self.tool.use_locDictReverse()

		# 房源介绍模板
		self.detailedHouseInfoTemplate = "\n##楼盘 {0}：\n**地址：{1} {2} {3} {4}\n**户型：{5}\n**面积：{6}\n**均价：{7}元/m²\n**更多详情：{8}\n-------------------------"

		# 首套房预算讨论空间
		self.firstHouse_cond = {'LPR': [self.LPR_list[0]], 'duration': self.duration_list[:3],
								'monthly': self.monthly_list[:2], 'loan': self.loan_list[:2]}
		# 非首套房预算讨论空间
		self.moreHouse_cond = {'LPR': [self.LPR_list[1]], 'duration': self.duration_list[1:],
							   'monthly': self.monthly_list[1:], 'loan': self.loan_list[1:]}

		self.g = Graph("http://localhost:7474", auth = ("neo4j", "Pine20210238"))

		self.averageArea = [(0, 0), (25, 30),
							(25, 30), (23, 28),
							(23, 28), (21, 26),
							(21, 26), (20, 25)]
		self.structureRate = [(0, 0), (0.1, 0.2),
							  (0.1, 0.2), (0.15, 0.25),
							  (0.15, 0.25), (0.2, 0.3),
							  (0.2, 0.3), (0.25, 0.35)]
		self.functionAdd = [(0, 0), (10, 20),
							(10, 20), (15, 25),
							(15, 25), (20, 30),
							(20, 30), (25, 35)]

		# 公共提问词
		self.budget_qwds = ['预算', '花销', '开销', '消费', '支出']
		self.area_qwds = ['平', '平方', '平米', '平方米', '面积', '占地', '大小']

		# 计算/筛选目标提问词
		self.house_qwds = ['房', '楼盘', '住宅', '住房']

		# 计算/筛选条件提问词
		self.plan_qwds = ['户型', '布局', '结构', '构造', '分布']
		self.ppl_qwds = ['人', '口', '人口', '人数']
		self.density_qwds = ["数量", "配套数", "配套量", "密度", "密集程度", "丰富度"]
		self.radius_qwds = ['半径', '范围', '距离']
		self.price_qwds = ['单价', '均价', '价格', '价钱', '报价', '参考价', '指导价',
						   '多少钱', '多少钱一平', '多少钱一平米', '多少钱一平方',
						   '多少钱一平米', '多少钱一平方米']

		# self.payroll_qwds = ['月入', '收入', '支出', '月薪', '年薪', '工资', '月收入', '年收入',
		# 					 '年入', '月支出', '年支出', '月工资', '年工资', ]

	# 计算器主函数
	def calculator_main(self):
		self.tool.print_prefix(
			"您已进入购房决策指标计算器，您需要依次输入您打算计算的内容和我需要您进一步提供的信息，也可以直接输入'退出'以离开计算器")
		target = self.identify_target()

		if target == 'exit':
			return 'exit'
		else:
			known_data = {'target': target}
			got_known = self.fetch_condition(target)
			while got_known['condition'] is None:
				got_known = self.fetch_condition(target)
			known_data.update(got_known)
			return self.workout_figure(known_data)

	# 传达查询结果
	def calculation_parser(self, response):
		query = ""
		parse_result = dict()
		if response == 'budget':
			message = input("#请输入您的购房预算范围（如'100-200万元'，'300-400W'等）：")
			pattern = r'^\s*(?:约|大概)?\s*(\d+\.?\d*)\s*(?:-|到|至)\s*(\d+\.?\d*)\s*(万|万元)?\s*$'
			match = re.compile(pattern).match(message)
			if not match:
				self.tool.print_prefix(f"#未能匹配您的输入: {message}，请重试")
				self.calculation_parser(response)
			else:
				start, end, unit = match.groups()

				start = int(start)
				end = int(end)
				if start > end:
					start, end = end, start
					self.tool.print_prefix("#已为您对调上下限")
				start = self.tool.convert_to_number(start, unit)
				end = self.tool.convert_to_number(end, unit)

				query = """
				MATCH (house:House)
				WITH house, 
					 SPLIT(SUBSTRING(house.floor_size, 1, SIZE(house.floor_size)-2), ', ') AS parts
				WITH house, 
					 toInterger(substring(parts[0], 1, size(parts[0])-2)) AS x, 
					 toInterger(substring(parts[1], 1, size(parts[1])-2)) AS y
				WHERE house.average_price > 0 AND x > 0 AND y > 0
				WITH house, 
					 house.average_price * x AS price_min, 
					 house.average_price * y AS price_max
				WITH house, price_min, price_max, 
					 (CASE WHEN price_max < {1} THEN price_max ELSE {1} END) 
					 - 
					 (CASE WHEN price_min > {0} THEN price_min ELSE {0} END) 
					 AS cross
				WITH house, cross, (CASE WHEN cross > 0 THEN cross ELSE 0 END) AS diff
				ORDER BY diff DESC
				LIMIT 3
				MATCH (r:Region {region_id: LEFT(house.house_id, 6)})
				RETURN house.house_name AS houseName,
					house.house_address AS houseAddress,
					house.average_price AS averagePrice,
					house.floor_plan AS floorPlan,
					house.floor_size AS floorSize,
					house.house_link AS houseLink,
					LEFT(house.house_id, 2) AS cityID,
					LEFT(house.house_id, 4) AS districtID,
					r.region_name AS regionName
				""".replace("{0}", str(start)).replace("{1}", str(end))
				parse_result.update({'data': (start, end)})

		elif response == 'area':
			message = input("#请输入您的购房面积筛选条件（如'80-120平米', '75到90平'）")
			pattern = r'^\s*(?:约|大概)?\s*(\d+\.?\d*)\s*(?:-|到|至)\s*(\d+\.?\d*)\s*(平|平方|平米|平方米)?\s*$'
			match = re.compile(pattern).match(message)
			if not match:
				self.tool.print_prefix(f"#未能匹配您的输入: {message}，请重试")
				self.calculation_parser(response)
			else:
				start, end, unit = match.groups()

				start = int(start)
				end = int(end)
				if start > end:
					start, end = end, start
					self.tool.print_prefix("#已为您对调上下限")

				query = """
				MATCH (h:House)
				WHERE h.floor_size IS NOT NULL
				WITH h, 
					 split(replace(substring(h.floor_size, 1, size(h.floor_size)-2), ' ', ''), ',') AS parts
				WITH h, 
					 toInteger(substring(parts[0], 1, size(parts[0])-2)) AS a,
					 toInteger(substring(parts[1], 1, size(parts[1])-2)) AS b
				WHERE a > 0 AND b > 0
				WITH h, a, b,
					 (CASE WHEN b < {1} THEN b ELSE {1} END) 
					 - 
					 (CASE WHEN a > {0} THEN a ELSE {0} END) 
					 AS cross
				WITH h, cross, (CASE WHEN cross > 0 THEN cross ELSE 0 END) AS diff
				ORDER BY diff DESC
				LIMIT 3
				MATCH (r:Region {region_id: LEFT(h.house_id, 6)})
				RETURN h.house_name AS houseName,
					h.house_address AS houseAddress,
					h.average_price AS averagePrice,
					h.floor_plan AS floorPlan,
					h.floor_size AS floorSize,
					h.house_link AS houseLink,
					LEFT(h.house_id, 2) AS cityID,
					LEFT(h.house_id, 4) AS districtID,
					r.region_name AS regionName
				""".replace("{0}", str(start)).replace("{1}", str(end))
				parse_result.update({'data': (start, end)})

		elif response == 'plan':
			message = input("#请直接输入一个整数n表示您心仪的户型（即n室）：")
			if not message.isnumeric():
				self.tool.print_prefix(f"未能匹配您的输入: {message}，请重试")
				self.calculation_parser(response)
			else:
				query = """
				MATCH (h:House)
				WHERE h.floor_plan CONTAINS '{0}' AND h.average_price > 0
				WITH h
				ORDER BY h.average_price
				LIMIT 3
				MATCH (r:Region {region_id: LEFT(h.house_id, 6)})
				RETURN h.house_name AS houseName,
					h.house_address AS houseAddress,
					h.average_price AS averagePrice,
					h.floor_plan AS floorPlan,
					h.floor_size AS floorSize,
					h.house_link AS houseLink,
					LEFT(h.house_id, 2) AS cityID,
					LEFT(h.house_id, 4) AS districtID,
					r.region_name AS regionName
				""".replace('{0}', message)
				parse_result.update({'data': message})

		elif response == 'density':
			message = input("#请直接输入一个整数n表示您希望房源附近至少有多少配套设施（阿拉伯数字）：")
			if not message.isnumeric():
				self.tool.print_prefix(f"未能匹配您的输入: {message}，请重试")
				self.calculation_parser(response)
			else:
				query = """
				MATCH (h:House)
				WITH h, 
					 size([(h)-[:H_NEAR_F]->(f:Facility) | f]) AS near_facility_count  // 统计关联设施数量
				WHERE near_facility_count >= 10 AND h.average_price > 0 // 筛选满足最低关联数的房屋
				MATCH (r:Region {region_id: LEFT(h.house_id, 6)})
				RETURN h.house_name AS houseName,
					h.house_address AS houseAddress,
					h.average_price AS averagePrice,
					h.floor_plan AS floorPlan,
					h.floor_size AS floorSize,
					h.house_link AS houseLink,
					LEFT(h.house_id, 2) AS cityID,
					LEFT(h.house_id, 4) AS districtID,
					r.region_name AS regionName
				ORDER BY h.average_price ASC  // 按均价升序排列（最低价优先）
				LIMIT 3
				""".replace("{0}", message)
				parse_result.update({'data': message})

		elif response == 'radius':
			message = input("#请直接输入一个整数n表示筛选距离（阿拉伯数字）：")
			if not message.isnumeric():
				self.tool.print_prefix(f"未能匹配您的输入: {message}，请重试")
				self.calculation_parser(response)
			else:
				query = """
				MATCH (h:House)-[r:H_NEAR_F]->(f:Facility)
				WHERE r.distance <= {0}  // 过滤距离≤n的关系
				WITH h, COUNT(r) AS valid_relations  // 统计有效关系数量
				ORDER BY valid_relations DESC  // 按数量降序排列
				LIMIT 3  // 取前三名
				MATCH (r:Region {region_id: LEFT(h.house_id, 6)})
				RETURN h.house_name AS houseName,
					h.house_address AS houseAddress,
					h.average_price AS averagePrice,
					h.floor_plan AS floorPlan,
					h.floor_size AS floorSize,
					h.house_link AS houseLink,
					LEFT(h.house_id, 2) AS cityID,
					LEFT(h.house_id, 4) AS districtID,
					r.region_name AS regionName
				""".replace("{0}", message)
				parse_result.update({'data': message})

		elif response == 'price':
			message = input("#请直接输入一个整数n表示您的单价（阿拉伯数字）：")
			if not message.isnumeric():
				self.tool.print_prefix(f"未能匹配您的输入: {message}，请重试")
				self.calculation_parser(response)
			else:
				query = """
				MATCH (h:House)
				WHERE h.average_price IS NOT NULL  // 过滤掉无均价的房屋
				WITH h, abs(h.average_price - {0}) AS price_diff  // 计算绝对差值
				ORDER BY price_diff ASC  // 按差值升序排列（最接近优先）
				LIMIT 3  // 取前三名
				MATCH (r:Region {region_id: LEFT(h.house_id, 6)})
				RETURN h.house_name AS houseName,
					h.house_address AS houseAddress,
					h.average_price AS averagePrice,
					h.floor_plan AS floorPlan,
					h.floor_size AS floorSize,
					h.house_link AS houseLink,
					LEFT(h.house_id, 2) AS cityID,
					LEFT(h.house_id, 4) AS districtID,
					r.region_name AS regionName
				""".replace("{0}", message)
				parse_result.update({'data': message})

		parse_result.update({'query': query})
		return parse_result

	# 获取计算/筛选条件
	def fetch_condition(self, target):
		none_condition = {'condition': None, 'value': None}
		if target == 'budget':
			self.tool.print_prefix("@您可通过月收入计算房款预算参考值")
			payroll = input("请输入您的月收入（建议您输入一个相对具体的数，如'10W', '9000'，'2.5万'等写法）：")
			# 正则表达式匹配
			pattern = r"^\s*(\d+\.?\d*)\s*(万|千|百万|k|K|m|M|w|W)?\s*$"
			payroll_regex = re.compile(pattern)
			match = payroll_regex.match(payroll)
			if not match:
				self.tool.print_prefix(f"#未能匹配您的输入: {payroll}，请重试")
				return none_condition
			else:
				amount, unit = match.groups()
				amount = float(amount)
				unit = 'None' if unit is None else unit
				unit = str.lower(unit) if unit.isalpha() else unit

				# 把计算过程交给workout_figure()
				result_value = self.tool.convert_to_number(amount, unit)
				result_cond = 'payroll'
				return {'condition': result_cond, 'value': result_value}

		elif target == 'area':
			self.tool.print_prefix("@您可通过居住人数计算购房面积参考值")
			ppl = input("#请输入您的居住人数预期（请直接输入阿拉伯数字）：")
			if ppl.isnumeric():
				# 把计算过程交给workout_figure()
				result_value = int(ppl) if int(ppl) < 7 else 7
				result_cond = 'population'
				return {'condition': result_cond, 'value': result_value}
			else:
				self.tool.print_prefix(f"#未能匹配您的输入: {ppl}，请重试")
				return none_condition

		elif target == 'house':
			self.tool.print_prefix("@您可通过户型、面积范围、预算范围、单价、配套距离范围、配套丰富度筛选楼盘信息")
			response = self.identify_target(False)
			got_info = self.calculation_parser(response)

			# 直接查询出结果，workout_figure()值负责组装
			result_cond = response
			result_value = self.g.run(got_info['query']).data()
			return {'condition': {'type': result_cond, 'data': got_info['data']}, 'value': result_value}

	# 计算指标
	def workout_figure(self, known_data):
		figure = ""
		if known_data['target'] == 'budget':
			payroll = known_data['value']
			loanFrame11 = self.tool.proceed_loanFrame(payroll, self.firstHouse_cond)
			loanFrame12 = self.tool.proceed_loanFrame(payroll, self.firstHouse_cond, mode = 2)
			loanFrame21 = self.tool.proceed_loanFrame(payroll, self.moreHouse_cond)
			loanFrame22 = self.tool.proceed_loanFrame(payroll, self.moreHouse_cond, mode = 2)
			loanFrame1 = pd.concat([loanFrame11, loanFrame12])
			loanFrame2 = pd.concat([loanFrame21, loanFrame22])

			figure += "$已知您的月收入为{0}元, 我为您计算了首套房和非首套房两种贷款情况（假定您仅使用公积金贷款）".format(
				known_data['value'])

			copyF1 = loanFrame1.rename(columns = {
				'LPR': 'LPR年利率(%)', 'duration': '贷款年限(年)', 'monthly': '月供占比(%)', 'loan': '贷款比例(%)',
			 'principal': '贷款本金(元)', 'interest': '贷款利息(元)', 'total': '贷款总额(元)', 'bgt': '房款预算(元)', 'method': "贷款方式"})
			copyF2 = loanFrame2.rename(columns = {
				'LPR': 'LPR年利率(%)', 'duration': '贷款年限(年)', 'monthly': '月供占比(%)', 'loan': '贷款比例(%)',
				'principal': '贷款本金(元)', 'interest': '贷款利息(元)', 'total': '贷款总额(元)', 'bgt': '房款预算(元)', 'method': "贷款方式"})

			figure += "\n$首套房贷款分类情况：\n" + tabulate(copyF1, headers = "keys", tablefmt = "grid",
															showindex = False, floatfmt=(",.3f", ",.0f", ",.0f", ",.0f",
																					   ",.0f", ",.0f", ",.0f", ",.0f"))
			figure += "\n$非首套房贷款分类情况：\n" + tabulate(copyF2, headers = "keys", tablefmt = "grid",
															showindex = False, floatfmt=(",.3f", ",.0f", ",.0f", ",.0f",
																					   ",.0f", ",.0f", ",.0f", ",.0f"))

			figure += "\n$您可以按需选择合适的贷款方案，为了便于您参考，我再将这两种情况各自的总预算中位数所对应的数据给您罗列出来"
			loanFrame1 = loanFrame1.sort_values(by = ['bgt'])
			loanFrame1["bgt"] = loanFrame1["bgt"].apply(lambda x: f"{x:,}")
			loanMedian1 = loanFrame1.iloc[len(loanFrame1) // 2]
			loanFrame2 = loanFrame2.sort_values(by = ['bgt'])
			loanMedian2 = loanFrame2.iloc[len(loanFrame2) // 2]
			loanFrame2["bgt"] = loanFrame2["bgt"].apply(lambda x: f"{x:,}")

			median_template = "\n**LPR年利率(%)：{0}\n**贷款年限(年)：{1}:\n**月供占比(%)：{2}\n**贷款比例(%)：{3}\n**贷款本金(元)：{4}\n**贷款利息(元)：{5}\n**贷款总额(元)：{6}\n**房款预算(元)：{7}\n**贷款方式：{8}"
			figure += "\n$首套房贷款中位数方案：" + median_template.format(
				loanMedian1['LPR'], loanMedian1['duration'], loanMedian1['monthly'], loanMedian1['loan'],
				loanMedian1['principal'], loanMedian1['interest'], loanMedian1['total'], loanMedian1['bgt'], loanMedian1['method'])
			figure += "$\n非首套房贷款中位数方案：" + median_template.format(
				loanMedian2['LPR'], loanMedian2['duration'], loanMedian2['monthly'], loanMedian2['loan'],
				loanMedian2['principal'], loanMedian2['interest'], loanMedian2['total'], loanMedian2['bgt'], loanMedian2['method'])

		elif known_data['target'] == 'area':
			population = known_data['value']
			areaFrame = self.tool.proceed_areaFrame(population, self.averageArea[population],
													self.structureRate[population], self.functionAdd[population])
			figure += "$已知您的居住人数预期为{0}人, 我为您计算了进行不同结构调整和功能加成的宜居面积".format(population)

			copyFrame = areaFrame.rename(columns = {
				'average': '人均面积(㎡)', 'structure+': '结构调整(㎡)',
				'function+': '功能加成(%)', 'total': '宜居面积(㎡)'})
			table = tabulate(copyFrame, headers = "keys", tablefmt = "grid", showindex = False)

			figure += "\n$宜居面积分类情况：\n" + table
			figure += "\n$您可以按需选择合适的宜居面积方案，为了便于您参考，我再将宜居面积中位数所对应的数据给您罗列出来"

			areaFrame = areaFrame.sort_values(by = ['total'])
			areaRow = areaFrame.iloc[len(areaFrame) // 2]

			median_template = "\n**人均面积(㎡)：{0}\n**结构调整(㎡)：{1}:\n**功能加成(%)：{2}\n**宜居面积(㎡)：{3}"
			figure += "\n$宜居面积中位数方案：" + median_template.format(
				areaRow['average'], areaRow['structure+'], areaRow['function+'], areaRow['total'])

		elif known_data['target'] == 'house':
			cond = known_data['condition']
			if cond['type'] == 'plan':
				figure += "$已知您心仪的户型是{0}室，我以单价最低为附加条件为您筛选出了以下房源".format(cond['data'])
			elif cond['type'] == 'radius':
				figure += "$已知您希望筛选在{0}米范围内内配套数量最多的房源，我为您找到了以下房源".format(cond['data'])
			elif cond['type'] == 'density':
				figure += "$已知您希望筛选周边有至少{0}项配套设施的房源，我为您找到了以下房源".format(cond['data'])
			elif cond['type'] == 'price':
				figure += "$已知您希望筛选单价在{0}元/㎡左右的房源，我为您找到了以下房源".format(cond['data'])
			elif cond['type'] == 'area':
				figure += "$已知您希望筛选面积在{0}-{1}㎡之间的房源，我为您找到了以下房源".format(cond['data'][0], cond['data'][1])
			elif cond['type'] == 'budget':
				figure += "$已知您希望筛选预算在{0}-{1}元之间的房源，我为您找到了以下房源".format(cond['data'][0], cond['data'][1])

			for query_info in known_data['value']:
				query_info.update({'cityName': self.locationDictReverse[query_info['cityID']]})
				del query_info['cityID']
				query_info.update({'districtName': self.locationDictReverse[query_info['districtID']]})
				del query_info['districtID']

				figure += self.detailedHouseInfoTemplate.format(
					query_info['houseName'], query_info['cityName'],
					query_info['districtName'], query_info['regionName'],
					query_info['houseAddress'],
					query_info['floorPlan'], query_info['floorSize'],
					query_info['averagePrice'], query_info['houseLink'])

		return figure

	def identify_target(self, mode = True):
		# mode值: 1 = 要计算的指标，2 = 提供的条件
		qst = "#请输入您要计算/筛选的指标：" if mode else "#请进一步选择您的筛选条件："
		inputTarget = input(qst)

		if inputTarget == '退出':
			return 'exit'
		else:
			if mode:  # 判断要计算的指标
				if self.check_words(self.budget_qwds, inputTarget):
					return 'budget'
				elif self.check_words(self.house_qwds, inputTarget):
					return 'house'
				elif self.check_words(self.area_qwds, inputTarget):
					return 'area'
				else:
					self.tool.print_prefix("@很抱歉我尚不能识别您输入的指标，请在下方重新输入")
					return self.identify_target(mode)
			else:  # 判断提供的条件
				if self.check_words(self.budget_qwds, inputTarget):
					return 'budget'
				elif self.check_words(self.plan_qwds, inputTarget):
					return 'plan'
				elif self.check_words(self.area_qwds, inputTarget):
					return 'area'
				elif self.check_words(self.radius_qwds, inputTarget):
					return 'radius'
				elif self.check_words(self.density_qwds, inputTarget):
					return 'density'
				elif self.check_words(self.price_qwds, inputTarget):
					return 'price'
				else:
					self.tool.print_prefix("很抱歉我尚不能识别您输入的指标，请在下方重新输入")
					return self.identify_target(mode)

	def check_words(self, wds, sent):
		for wd in wds:
			if wd in sent:
				return True
		return False


if __name__ == '__main__':
	gt = GoodTools("Prefix:", "Default Message")
	figCal = FigureCaculator(gt)
	result = figCal.calculator_main()
	figCal.tool.print_preix(result)
