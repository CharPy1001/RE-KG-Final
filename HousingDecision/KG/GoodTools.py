# Editor:CharPy
# Edit time:2025/4/8 21:21
import pandas as pd

class GoodTools:

	def __init__(self, prefix, default):
		districtTable = pd.read_csv('../Data/PureTable/Districts.csv')
		cityTable = pd.read_csv('../Data/PureTable/Cities.csv')
		regionTable = pd.read_csv('../Data/PureTable/Regions.csv')[['region_name', 'region_id']]

		# 由名字查编号
		self.locDict = dict()
		self.locDict.update(districtTable.set_index('district_name')['district_id'].to_dict())
		self.locDict.update(cityTable.set_index('city_name')['city_id'].to_dict())
		self.locDict.update(regionTable.set_index('region_name')['region_id'].to_dict())

		# 由编号查名字
		self.locDictReverse = dict()
		self.locDictReverse.update(districtTable.set_index('district_id')['district_name'].to_dict())
		self.locDictReverse.update(cityTable.set_index('city_id')['city_name'].to_dict())
		self.locDictReverse.update(regionTable.set_index('region_id')['region_name'].to_dict())

		self.default = default
		self.prefix = prefix

		self.loc_set = set(self.locDict.keys())
		self.dev_set = set([i.strip() for i in open('../Dict/developer.txt', encoding = 'utf-8') if i.strip()])

	def use_loc(self):
		return set(self.locDict.keys())

	def use_locDict(self):
		return self.locDict

	def use_locDictReverse(self):
		return self.locDictReverse

	def use_dev(self):
		return self.dev_set

	def use_fac(self):
		return {"教育", "商业", "医疗", "交通"}

	# 连带前缀打印
	def print_prefix(self, info):
		print(self.prefix, info)

	def use_default(self):
		return self.default

	# 单位转换
	def convert_to_number(self, amount_str, unit):
		amount = float(amount_str)
		if unit in ("万", "万元", "w"):
			return amount * 10000
		elif unit in ("千", "千元", "k"):
			return amount * 1000
		elif unit in ("百万", "百万元", "m"):
			return amount * 1000000
		elif unit in ("千万", "千万元", "kw"):
			return amount * 10000000
		elif unit in ("亿", "亿元", "y"):
			return amount * 100000000
		return amount

	def proceed_areaFrame(self, population, average, structure, function):
		table = {'average': [], 'structure+': [], 'function+': [], 'total': []}
		for avg in average:
			for stru in structure:
				for func in function:
					table['average'].append(int(avg))
					table['structure+'].append(int(stru*100))
					table['function+'].append(int(func))
					table['total'].append(int(population * avg * (1 + stru) + func))

		return pd.DataFrame(table)
	# 贷款量计算

	def workout_loan(self, payroll, lpr, dr, m, mode):

		"""
		lpr: 年贷款利率，需要除以12
		dr: 贷款年限，需要乘以12
		m: 月供占月收入比例
		"""

		lpr = round(lpr/12, 4)
		dr *= 12
		common = (1+lpr) ** dr
		month_payment = m * payroll
		if mode == 1:  # 等额本息方式，总利息相比等额本金较高
			principal = month_payment * (common - 1) / (lpr * common)
			total = month_payment * dr
			return {'principal': principal, 'interest': total - principal,
					'total': total}
		elif mode == 2:  # 等额本金方式，总利息相比等额本息较低
			principal = month_payment / (lpr + 1 / dr)
			interest = (month_payment * lpr * (dr + 1)) / (2 * (1 / dr + lpr))
			return {'principal': principal, 'interest': interest,
					'total': principal + interest}

	def proceed_loanFrame(self, payroll, copyCond, mode = 1):
		# mode: 1 = 等额本息，2 = 等额本金
		cond = {'LPR': [], 'duration': [], 'monthly': [], 'loan': [], 'principal': [],
				'interest': [], 'total': [], 'bgt': [], 'method': "等额本息" if mode == 1 else "等额本金"}
		for lpr in copyCond['LPR']:
			for dr in copyCond['duration']:
				for m in copyCond['monthly']:
					for ln in copyCond['loan']:
						result = self.workout_loan(payroll, lpr, dr, m, mode)
						cond['LPR'].append(str(lpr))
						cond['duration'].append(dr)
						cond['monthly'].append(int(m*100))
						cond['loan'].append(int(ln*100))
						cond['principal'].append(int(result['principal']))
						cond['interest'].append(int(result['interest']))
						cond['total'].append(int(result['total']))
						cond['bgt'].append(int(result['principal'] / ln))

		return pd.DataFrame(cond)


if __name__ == '__main__':
	pass
