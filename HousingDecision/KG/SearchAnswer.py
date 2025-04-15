# Editor:CharPy
# Edit time:2025/4/7 12:07

from py2neo import Graph
from GoodTools import *

class AnswerSearcher:
	def __init__(self, tool):
		self.g = Graph("http://localhost:7474", auth = ("neo4j", "Pine20210238"))
		self.num_limit = 20

		districtTable = pd.read_csv('../Data/PureTable/Districts.csv')
		cityTable = pd.read_csv('../Data/PureTable/Cities.csv')
		regionTable = pd.read_csv('../Data/PureTable/Regions.csv')[['region_name', 'region_id']]

		self.tool = tool

		self.locationDictReverse = self.tool.use_locDictReverse()
		self.locationDictReverse.update(districtTable.set_index('district_id')['district_name'].to_dict())
		self.locationDictReverse.update(cityTable.set_index('city_id')['city_name'].to_dict())
		self.locationDictReverse.update(regionTable.set_index('region_id')['region_name'].to_dict())

		self.houseLocationTemplate = "&楼盘 {0} 位于 {1}市 {2}区 {3}地区，地址为 {4}。"
		self.facilityLocationTemplate = "&{0}配套 {1} 位于 {2}市 {3}区 {4}地区。"
		self.unspecificFacilityTemplate = "\n**{0}配套：{1}，距离当前楼盘{2}米"
		self.specificFacilityTemplate = "\n**{0}，距离当前楼盘{1}米"
		self.singleFacilityTemplate = "\n**{0}配套：{1}"
		self.simpleHouseInfoTemplate = "\n##楼盘 {0}：\n**地址：{1}\n**户型：{2}\n**面积：{3}\n**均价：{4}元/m²\n**更多详情：{5}\n-------------------------"
		self.detailedHouseInfoTemplate = "\n##楼盘 {0}：\n**地址：{1} {2} {3} {4}\n**户型：{5}\n**面积：{6}\n**均价：{7}元/m²\n**更多详情：{8}\n-------------------------"
		self.locationPriceTemplate = "\n& {0} 的楼盘均价为 {1} 元/m²"

	'''执行cypher查询，并返回相应结果'''

	def search_main(self, sqls):
		final_answers = []
		for sql_ in sqls:
			question_type = sql_['question_type']
			queries = sql_['sql']
			answers = []
			for query in queries:
				res = self.g.run(query).data()
				answers += res
			final_answer = self.answer_prettify(question_type, answers)
			if final_answer:
				final_answers.append(final_answer)
		return final_answers

	'''根据对应的qustion_type，调用相应的回复模板'''

	def answer_prettify(self, question_type, answers):
		final_answer = ""
		if not answers:
			return ''

		if question_type == 'house_location':
			# 能到这一步的一定有且只有答案
			rough_answer = answers[0]
			rough_answer.update({'cityName': self.locationDictReverse[rough_answer['cityID']]})
			del rough_answer['cityID']
			rough_answer.update({'districtName': self.locationDictReverse[rough_answer['districtID']]})
			del rough_answer['districtID']
			final_answer = self.houseLocationTemplate. \
				format(rough_answer['houseName'], rough_answer['cityName'],
					   rough_answer['districtName'], rough_answer['regionName'],
					   rough_answer['houseAddress'])

		elif question_type == 'facility_location':
			# 能到这一步的一定有且只有答案
			rough_answer = answers[0]
			rough_answer.update({'cityName': self.locationDictReverse[rough_answer['cityID']]})
			del rough_answer['cityID']
			rough_answer.update({'districtName': self.locationDictReverse[rough_answer['districtID']]})
			del rough_answer['districtID']
			final_answer = self.facilityLocationTemplate. \
				format(rough_answer['facilityType'], rough_answer['facilityName'],
					   rough_answer['cityName'], rough_answer['districtName'],
					   rough_answer['regionName'])

		elif question_type == 'house_facility':
			# 这部分答案数量不定
			if answers:
				final_answer = "楼盘 {0} 的配套情况如下：".format(answers[0]['houseName'])
				for rough_answer in answers:
					final_answer += self.unspecificFacilityTemplate.format(rough_answer['facilityType'],
						rough_answer['facilityName'], rough_answer['distance'])
			else:
				final_answer = "未找到楼盘 {0} 周边的相关配套".format(answers[0]['houseName'])

		elif question_type == 'house_business':
			# 这部分答案数量不定
			if answers:
				final_answer = "楼盘 {0} 的商业配套情况如下：".format(answers[0]['houseName'])
				for rough_answer in answers:
					final_answer += self.specificFacilityTemplate.format(
						rough_answer['facilityName'], rough_answer['distance'])
			else:
				final_answer = "未找到楼盘 {0} 周边的商业配套".format(answers[0]['houseName'])

		elif question_type == 'house_traffic':
			# 这部分答案数量不定
			if answers:
				final_answer = "楼盘 {0} 的交通配套情况如下：".format(answers[0]['houseName'])
				for rough_answer in answers:
					final_answer += self.specificFacilityTemplate.format(
						rough_answer['facilityName'], rough_answer['distance'])
			else:
				final_answer = "未找到楼盘 {0} 周边的交通配套".format(answers[0]['houseName'])

		elif question_type == 'house_hospital':
			# 这部分答案数量不定
			if answers:
				final_answer = "楼盘 {0} 的医疗配套情况如下：".format(answers[0]['houseName'])
				for rough_answer in answers:
					final_answer += self.specificFacilityTemplate.format(
						rough_answer['facilityName'], rough_answer['distance'])
			else:
				final_answer = "未找到楼盘 {0} 周边的医疗配套".format(answers[0]['houseName'])

		elif question_type == 'house_school':
			# 这部分答案数量不定
			if answers:
				final_answer = "楼盘 {0} 的教育配套情况如下：".format(answers[0]['houseName'])
				for rough_answer in answers:
					final_answer += self.specificFacilityTemplate.format(
						rough_answer['facilityName'], rough_answer['distance'])
			else:
				final_answer = "未找到楼盘 {0} 周边的教育配套".format(answers[0]['houseName'])

		elif question_type == 'house_primarySchool':
			# 这部分答案数量不定
			if answers:
				final_answer = "楼盘 {0} 周边有以下小学：".format(answers[0]['houseName'])
				for rough_answer in answers:
					final_answer += self.specificFacilityTemplate.format(
						rough_answer['facilityName'], rough_answer['distance'])
			else:
				final_answer = "未找到楼盘 {0} 周边的小学".format(answers[0]['houseName'])

		elif question_type == 'house_middleSchool':
			# 这部分答案数量不定
			if answers:
				final_answer = "楼盘 {0} 周边有以下中学：".format(answers[0]['houseName'])
				for rough_answer in answers:
					final_answer += self.specificFacilityTemplate.format(
						rough_answer['facilityName'], rough_answer['distance'])
			else:
				final_answer = "未找到楼盘 {0} 周边的中学".format(answers[0]['houseName'])

		elif question_type == 'house_kindergarten':
			# 这部分答案数量不定
			if answers:
				final_answer = "楼盘 {0} 周边有以下幼儿园：".format(answers[0]['houseName'])
				for rough_answer in answers:
					final_answer += self.specificFacilityTemplate.format(
						rough_answer['facilityName'], rough_answer['distance'])
			else:
				final_answer = "未找到楼盘 {0} 周边的幼儿园".format(answers[0]['houseName'])

		elif question_type == 'facility_house':
			# 能到这一步的一定至少有一个答案
			final_answer = "与{0}配套 {1} 关联的个别楼盘信息如下：".format(answers[0]['facilityType'], answers[0]['facilityName'])
			for rough_answer in answers:
				# 户型信息排版（如果有）
				floorPlanInfo = ""
				floorPlanTemplate = "{0}室/"
				for elem in eval(rough_answer['floorPlan']):
					if eval(elem) > 0:
						floorPlanInfo += floorPlanTemplate.format(elem)
				# 面积信息排版（如果有）
				floorSizeInfo = ""
				floorSizeTemplate = "{0}-{1}㎡"
				sizeInfo = eval(rough_answer['floorSize'])
				if eval(sizeInfo[0]) > 0 and eval(sizeInfo[1]) > 0:
					floorSizeInfo += floorSizeTemplate.format(sizeInfo[0], sizeInfo[1])
				# 处理没有报价的情况
				if int(rough_answer['averagePrice']) == 0:
					rough_answer['averagePrice'] = "暂无报价"
				# 组装
				final_answer += self.simpleHouseInfoTemplate.format(
					rough_answer['houseName'], rough_answer['houseAddress'],
					rough_answer['floorPlan'], rough_answer['floorSize'],
					rough_answer['averagePrice'], rough_answer['houseLink'])

		elif question_type == 'location_house':
			# 个别地区可能没有答案
			if answers:
				tempID = answers[0]['locationID']
				locationTemplate = "{0}{1}".replace("{0}", self.locationDictReverse[tempID])
				if len(tempID) == 2:
					locationTemplate = locationTemplate.replace("{1}", "市")
				elif len(tempID) == 4:
					locationTemplate = locationTemplate.replace("{1}", "区")
				elif len(tempID) == 6:
					locationTemplate = locationTemplate.replace("{1}", "地区")
				final_answer = "位于 {0} 的个别楼盘信息如下：".format(locationTemplate)

				for rough_answer in answers:
					# 户型信息排版（如果有）
					floorPlanInfo = ""
					floorPlanTemplate = "{0}室/"
					for elem in eval(rough_answer['floorPlan']):
						if eval(elem) > 0:
							floorPlanInfo += floorPlanTemplate.format(elem)
					# 面积信息排版（如果有）
					floorSizeInfo = ""
					floorSizeTemplate = "{0}-{1}㎡"
					sizeInfo = eval(rough_answer['floorSize'])
					if eval(sizeInfo[0]) > 0 and eval(sizeInfo[1]) > 0:
						floorSizeInfo += floorSizeTemplate.format(sizeInfo[0], sizeInfo[1])
					# 处理没有报价的情况
					if int(rough_answer['averagePrice']) == 0:
						rough_answer['averagePrice'] = "暂无报价"
					# 组装
					final_answer += self.simpleHouseInfoTemplate.format(
						rough_answer['houseName'], rough_answer['houseAddress'],
						rough_answer['floorPlan'], rough_answer['floorSize'],
						rough_answer['averagePrice'], rough_answer['houseLink'])

		elif question_type == 'location_facility':
			# 个别地区可能没有答案
			if answers:
				tempID = answers[0]['locationID']
				locationTemplate = "{0}{1}".replace("{0}", self.locationDictReverse[tempID])
				if len(tempID) == 2:
					locationTemplate = locationTemplate.replace("{1}", "市")
				elif len(tempID) == 4:
					locationTemplate = locationTemplate.replace("{1}", "区")
				elif len(tempID) == 6:
					locationTemplate = locationTemplate.replace("{1}", "地区")
				final_answer = "位于 {0} 的个别配套信息如下：".format(locationTemplate)
				# 组装
				for rough_answer in answers:
					final_answer += self.singleFacilityTemplate.format(
						rough_answer['facilityType'], rough_answer['facilityName'])

		elif question_type == 'location_price':
			# 能到这一步的至多一个答案
			if answers:
				tempID = answers[0]['locationID']
				locationTemplate = "{0}{1}".replace("{0}", self.locationDictReverse[tempID])
				if len(tempID) == 2:
					locationTemplate = locationTemplate.replace("{1}", "市")
				elif len(tempID) == 4:
					locationTemplate = locationTemplate.replace("{1}", "区")
				elif len(tempID) == 6:
					locationTemplate = locationTemplate.replace("{1}", "地区")

				final_answer = self.locationPriceTemplate.format(locationTemplate, answers[0]['avgPrice'])

		elif question_type == 'developer_house':
			# 能到这一步的一定至少有一个答案
			final_answer = "由 {0} 开发的个别楼盘信息如下：".format(answers[0]['devName'])

			for rough_answer in answers:
				# 户型信息排版（如果有）
				floorPlanInfo = ""
				floorPlanTemplate = "{0}室/"
				for elem in eval(rough_answer['floorPlan']):
					if eval(elem) > 0:
						floorPlanInfo += floorPlanTemplate.format(elem)
				# 面积信息排版（如果有）
				floorSizeInfo = ""
				floorSizeTemplate = "{0}-{1}㎡"
				sizeInfo = eval(rough_answer['floorSize'])
				if eval(sizeInfo[0]) > 0 and eval(sizeInfo[1]) > 0:
					floorSizeInfo += floorSizeTemplate.format(sizeInfo[0], sizeInfo[1])

				rough_answer.update({'cityName': self.locationDictReverse[rough_answer['cityID']]})
				del rough_answer['cityID']
				rough_answer.update({'districtName': self.locationDictReverse[rough_answer['districtID']]})
				del rough_answer['districtID']
				# 组装
				final_answer += self.detailedHouseInfoTemplate.format(
					rough_answer['houseName'], rough_answer['cityName'],
					rough_answer['districtName'], rough_answer['regionName'],
					rough_answer['houseAddress'],
					rough_answer['floorPlan'], rough_answer['floorSize'],
					rough_answer['averagePrice'], rough_answer['houseLink'])

		elif question_type == 'house_information':
			# 能到这一步的有且只有一个答案
			rough_answer = answers[0]
			rough_answer.update({'cityName': self.locationDictReverse[rough_answer['cityID']]})
			del rough_answer['cityID']
			rough_answer.update({'districtName': self.locationDictReverse[rough_answer['districtID']]})
			del rough_answer['districtID']

			final_answer = self.detailedHouseInfoTemplate.format(
				rough_answer['houseName'], rough_answer['cityName'],
				rough_answer['districtName'], rough_answer['regionName'],
				rough_answer['houseAddress'],
				rough_answer['floorPlan'], rough_answer['floorSize'],
				rough_answer['averagePrice'], rough_answer['houseLink'])

		return final_answer


if __name__ == '__main__':
	gt = GoodTools("Prefix:", "Default Message")
	searcher = AnswerSearcher(gt)
