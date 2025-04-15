# Editor:CharPy
# Edit time:2025/3/7 8:56
import re

import pandas as pd

fFrame = pd.read_csv('../Data/PureTable/Facilities.csv')
hFrame = pd.read_csv('../Data/PureTable/Houses.csv')
rFrame = pd.read_csv('../Data/PureTable/Regions.csv')
vList = ['万科', '保利', '华润', '招商', '中建', '铁建', '越秀',
		 '碧桂园', '中海', '金地', '珠江', '鹏瑞', '美的', '合生',
		 '华侨城', '龙湖', '深铁', '天健', '绿城', '京基', '鸿荣源',
		 '顺控', '新世界', '远洋', '华夏', '金科', '融创', '富力']
cList = ['广州', '佛山', '深圳']
dList = ['越秀', '天河', '海珠区', '荔湾', '白云', '黄埔', '番禺', '花都', '增城', '从化',
		 '禅城', '南海', '顺德', '三水', '高明',
		 '罗湖', '福田', '南山区', '宝安', '龙岗', '盐田', '龙华', '坪山', '光明', '大鹏']


def strip_house(frame):
	return {'house.txt': frame['house_name'].to_list()}


def strip_region(frame):
	return {'region.txt': frame['region_name'].to_list()}


def strip_facility(frame):
	trafficList = frame[frame['facility_type'] == '交通']['facility_name'].tolist()
	businessList = frame[frame['facility_type'] == '商业']['facility_name'].tolist()
	schoolList = frame[frame['facility_type'] == '教育']['facility_name'].tolist()
	medicalList = frame[frame['facility_type'] == '医疗']['facility_name'].tolist()

	middleSchoolList, primarySchoolList, kindergartenList = [], [], []
	for item in schoolList:
		match = re.search(r'【(中学|小学|幼儿园)】(.+)', item)
		if match:
			category = match.group(1)
			name = match.group(2)
			if category == '中学':
				middleSchoolList.append(name)
			elif category == '小学':
				primarySchoolList.append(name)
			elif category == '幼儿园':
				kindergartenList.append(name)

	return {'traffic.txt': trafficList,
			'business.txt': businessList,
			'middleSchool.txt': middleSchoolList,
			'primarySchool.txt': primarySchoolList,
			'kindergarten.txt': kindergartenList,
			'hospital.txt': medicalList}


if __name__ == '__main__':
	path = './'
	lists = dict()
	lists.update(strip_house(hFrame))
	lists.update(strip_region(rFrame))
	lists.update(strip_facility(fFrame))
	lists.update({'developer.txt': vList,
				  'city.txt': cList,
				  'district.txt': dList})

	for path in lists.keys():
		with open('./' + path, 'w', encoding = 'utf-8') as f:
			for word in lists[path]:
				f.write("%s\n" % word)
