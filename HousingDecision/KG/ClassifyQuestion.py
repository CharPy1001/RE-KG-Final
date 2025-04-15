# Editor:CharPy

import os
import ahocorasick

class QuestionClassifier:
	def __init__(self, default_message):
		self.default_message = default_message

		'''特征词路径'''
		cur_path = '../Dict/'
		self.business_path = os.path.join(cur_path, 'business.txt')
		self.city_path = os.path.join(cur_path, 'city.txt')
		self.developer_path = os.path.join(cur_path, 'developer.txt')
		self.district_path = os.path.join(cur_path, 'district.txt')
		self.hospital_path = os.path.join(cur_path, 'hospital.txt')
		self.house_path = os.path.join(cur_path, 'house.txt')
		self.kindergarten_path = os.path.join(cur_path, 'kindergarten.txt')
		self.middleSchool_path = os.path.join(cur_path, 'middleSchool.txt')
		self.primarySchool_path = os.path.join(cur_path, 'primarySchool.txt')
		self.region_path = os.path.join(cur_path, 'region.txt')
		self.traffic_path = os.path.join(cur_path, 'traffic.txt')

		'''加载特征词'''
		self.city_wds = [i.strip() for i in open(self.city_path, encoding = 'utf-8') if i.strip()]
		self.district_wds = [i.strip() for i in open(self.district_path, encoding = 'utf-8') if i.strip()]
		self.region_wds = [i.strip() for i in open(self.region_path, encoding = 'utf-8') if i.strip()]
		self.location_wds = self.city_wds + self.district_wds + self.region_wds
		self.house_wds = [i.strip() for i in open(self.house_path, encoding = 'utf-8') if i.strip()]
		self.developer_wds = [i.strip() for i in open(self.developer_path, encoding = 'utf-8') if i.strip()]
		self.hospital_wds = [i.strip() for i in open(self.hospital_path, encoding = 'utf-8') if i.strip()]
		self.business_wds = [i.strip() for i in open(self.business_path, encoding = 'utf-8') if i.strip()]
		self.traffic_wds = [i.strip() for i in open(self.traffic_path, encoding = 'utf-8') if i.strip()]
		self.kindergarten_wds = [i.strip() for i in open(self.kindergarten_path, encoding = 'utf-8') if i.strip()]
		self.middleSchool_wds = [i.strip() for i in open(self.middleSchool_path, encoding = 'utf-8') if i.strip()]
		self.primarySchool_wds = [i.strip() for i in open(self.primarySchool_path, encoding = 'utf-8') if i.strip()]
		self.school_wds = self.kindergarten_wds + self.middleSchool_wds + self.primarySchool_wds
		self.facility_wds = self.business_wds + self.school_wds \
								+ self.hospital_wds + self.traffic_wds

		'''结构化捕获词和评估模式捕获词'''
		self.calculation_kwds = ['数据计算']
		self.evaluation_kwds = ['需求评估']

		self.actree_wds = set(self.house_wds + self.facility_wds
								+ self.developer_wds + self.location_wds
							  + self.calculation_kwds + self.evaluation_kwds)
		self.tree = self.build_actree(list(self.actree_wds))  # 构造领域actree
		self.wdtype_dict = self.build_wdtype_dict()  # 构建词典

		'''非结构化提问词'''
		self.price_qwds = ['单价', '均价', '价格', '价钱', '报价', '参考价', '指导价',
						   '多少钱', '多少钱一平', '多少钱一平米', '多少钱一平方',
						   '多少钱一平米', '多少钱一平方米']
		self.developer_qwds = ['开发商', '房地产商', '谁家', '哪家']
		self.house_qwds = ['房', '楼盘', '住宅', '住房']

		self.facility_qwds = ['配套', '设施', '场所', '服务']
		self.primarySchool_qwds = ['小学']
		self.middleSchool_qwds = ['中学']
		self.kindergarten_qwds = ['幼儿园', '托儿所']
		self.school_qwds = ['学校', '学区']
		self.hospital_qwds = ['医院', '诊所', '药店', '药房', '卫生站', '卫生所',
							  '急救中心', '医疗中心', '康复中心', '疗养院']
		self.business_qwds = ['购物', '超市', '中心', '商场', '市场',
							  '商业街', '商超']
		self.traffic_qwds = ['交通', '公交', '地铁', '路程', '步行', '驾车', '距离', '直线距离']

		self.region_qwds = ['地区', '村', '镇', '乡', '街', '路', '巷', '弄', '号', '岗']
		self.district_qwds = ['区', '县']
		self.city_qwds = ['市', '州', '城市']
		self.location_qwds = ['哪里', '位处', '位于'] + self.region_qwds + self.district_qwds + self.city_qwds

		print('model init finished ......')
		print('Charlie:', default_message)

	'''分类主函数'''

	def classifier_main(self, qst):
		decision_dict = self.check_decision(qst)
		if not decision_dict:
			return {}

		# 收集问句当中所涉及到的实体类型
		types = []
		for t in decision_dict.values():
			types += t

		qst_types = []

		'''
		非结构化问题分类
		'''

		# 已知房源名字，求其所在城市/辖区/地区
		if self.check_words(self.location_qwds, qst) and 'house' in types:
			qst_types.append('house_location')
		# 已知配套名字，求其所在城市/辖区/地区
		if self.check_words(self.location_qwds, qst) and 'facility' in types:
			qst_types.append('facility_location')
		# 已知房源名字，求其配套
		if self.check_words(self.facility_qwds, qst) and 'house' in types:
			qst_types.append('house_facility')
		# 已知房源名字，求附近的商业配套
		if self.check_words(self.business_qwds, qst) and 'house' in types:
			qst_types.append('house_business')
		# 已知房源名字，求附近的医疗配套
		if self.check_words(self.hospital_qwds, qst) and 'house' in types:
			qst_types.append('house_hospital')
		# 已知房源名字，求附近的交通配套
		if self.check_words(self.traffic_qwds, qst) and 'house' in types:
			qst_types.append('house_traffic')
		# 已知房源的名字，求附近的教育配套
		if self.check_words(self.school_qwds, qst) and 'house' in types:
			qst_types.append('house_school')
		# 已知房源的名字，求附近的幼儿园
		if self.check_words(self.kindergarten_qwds, qst) and 'house' in types:
			qst_types.append('house_kindergarten')
		# 已知房源的名字，求附近的中学
		if self.check_words(self.middleSchool_qwds, qst) and 'house' in types:
			qst_types.append('house_middleSchool')
		# 已知房源的名字，求附近的小学
		if self.check_words(self.primarySchool_qwds, qst) and 'house' in types:
			qst_types.append('house_primarySchool')
		# 已知配套名字，求与其相连的房源
		if self.check_words(self.house_qwds, qst) and 'facility' in types:
			qst_types.append('facility_house')
		# 已知城市/辖区/地区，求房源
		if self.check_words(self.house_qwds, qst) and 'location' in types:
			qst_types.append('location_house')
		# 已知城市/辖区/地区，求配套
		if self.check_words(self.facility_qwds, qst) and 'location' in types:
			qst_types.append('location_facility')
		# 已知城市/辖区/地区，求其房屋均价
		if self.check_words(self.price_qwds, qst) and 'location' in types:
			qst_types.append('location_price')
		# 已知开发商名字，求房源
		if self.check_words(self.house_qwds, qst) and 'developer' in types:
			qst_types.append('developer_house')

		'''
		结构化问题和评估模式捕捉
		'''

		if 'calculation' in types:
			qst_types.append('calculation')
		if 'evaluation' in types:
			qst_types.append('evaluation')

		# 如果同时捕捉到则直接置空（宕机）
		if 'calculation' in qst_types and 'evaluation' in qst_types:
			qst_types = []
		else:
			if 'calculation' in qst_types:  # 捕捉到结构化计算问题关键词，且无评估模式关键词
				qst_types = ['calculation']
			elif 'evaluation' in qst_types:  # 捕捉到评估模式关键词，且无结构化计算问题关键词
				qst_types = ['evaluation']

		'''
		兜底措施
		'''

		if not qst_types:
			if 'house' in types:
				qst_types.append('house_information')

			if 'location' in types:
				qst_types.append('location_house')

			if 'facility' in types:
				qst_types.append('facility_location')

			if 'developer' in types:
				qst_types.append('developer_house')

		# 将多个分类结果进行合并处理，组装成一个字典
		res_classify = dict()
		res_classify['args'] = decision_dict
		res_classify['question_types'] = qst_types

		return res_classify

	'''构造词对应的类型'''

	def build_wdtype_dict(self):
		wdtype_dict = dict()
		for wd in self.actree_wds:
			wdtype_dict[wd] = []
			if wd in self.developer_wds:
				wdtype_dict[wd].append('developer')
			if wd in self.house_wds:
				wdtype_dict[wd].append('house')
			if wd in self.facility_wds:
				wdtype_dict[wd].append('facility')
			if wd in self.location_wds:
				wdtype_dict[wd].append('location')
			if wd in self.calculation_kwds:
				wdtype_dict[wd].append('calculation')
			if wd in self.evaluation_kwds:
				wdtype_dict[wd].append('evaluation')

		return wdtype_dict

	'''构造actree以加速过滤'''

	def build_actree(self, wordlist):
		actree = ahocorasick.Automaton()
		for index, word in enumerate(wordlist):
			actree.add_word(word, (index, word))
		actree.make_automaton()
		return actree

	'''问句过滤'''

	def check_decision(self, qst):
		iter_wds = []
		for it in self.tree.iter(qst):
			wd = it[1][1]
			iter_wds.append(wd)
		stop_wds = []
		for wd1 in iter_wds:
			for wd2 in iter_wds:
				if wd1 in wd2 and wd1 != wd2:
					stop_wds.append(wd1)
		final_wds = [_ for _ in iter_wds if _ not in stop_wds]
		final_dict = {_: self.wdtype_dict.get(_) for _ in final_wds}

		return final_dict

	'''基于特征词进行分类'''

	def check_words(self, wds, sent):
		for wd in wds:
			if wd in sent:
				return True
		return False


if __name__ == '__main__':
	default = '您好，我是购房决策小助手Charlie，前来为您答疑解惑，如我未能明白您的意思还请多多体谅~'
	default += '\n@ps: 输入“数据计算”可进入购房决策指标计算器，输入“需求评估”可进入房源评估程序'

	handler = QuestionClassifier(default)
	while 1:
		question = input('input an question:')
		data = handler.classifier_main(question)
		print(data)
