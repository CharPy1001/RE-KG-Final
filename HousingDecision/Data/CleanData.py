# Editor:CharPy

import pandas as pd
import re
import os

# 导入
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)


# 制作 Regions.csv
def region_csv(homeFrame, districtCopy):
	regionFrame = homeFrame.drop(['project_name', 'floor_message', 'project_link', 'average_price',
								  'facility_type', 'facility_name', 'distance'], axis = 1). \
		drop_duplicates(subset = 'project_location')  # 保留必要行，按地点去重
	regionFrame['region_label'] = regionFrame['project_location'].str.extract(r'\[(.*?)\]')  # 用正则表达式提取
	regionFrame['region_label'] = regionFrame['region_label'].str.split()  # 提取内容包含市辖区和区内小地区
	regionFrame['district_name'] = regionFrame['region_label'].str[0]  # 提取市辖区
	regionFrame['region_name'] = regionFrame['region_label'].str[1]  # 提取区内小地区

	# 按照市辖区合并
	regionFrame = pd.merge(regionFrame, districtCopy, left_on = 'district_name', right_on = 'district_name',
						   how = 'left')
	regionFrame = regionFrame.drop_duplicates(subset = 'region_name').drop(['region_label'], axis = 1)  # 按区内小地区去重
	regionFrame['region_id'] = [None] * len(regionFrame)  # 提前新开一列
	districtCount = list(regionFrame['district_id'].unique())  # 统计有多少个不重复的市辖区

	# 对地区进行编号
	for item in districtCount:
		indices = regionFrame.loc[regionFrame['district_id'] == item].index.tolist()  # 列出当前市辖区下的所有小地区
		number = 1  # 自增变量
		for idx in indices:
			# 将左侧补0的2位数字编号追加到4位市辖区id后，形成6位地区编号
			regionFrame.loc[idx, 'region_id'] = regionFrame.loc[idx, 'district_id'] + str(number).zfill(2)
			number += 1
	regionFrame = regionFrame[regionFrame['region_id'].notna()]  # 把没有获得地区编号的行删除
	return regionFrame.drop(['project_location', 'district_id'], axis = 1)  # 删除多余列


# 制作 Facilities.csv
def facility_csv(homeFrame, regionCopy):
	# 保留必要列，按配套名去重，删除空行
	facilityFrame = homeFrame.drop(['project_name', 'floor_message', 'project_link', 'average_price', 'distance'],
								   axis = 1). \
		dropna(subset = ['facility_name']).drop_duplicates(subset = 'facility_name')  # 保留必要行，按配套名删除空行并去重
	facilityFrame['facility_type'] = homeFrame['facility_type'].fillna("医疗")  # 经观察，源数据中类型值为空的配套全部为医疗配套
	facilityFrame['region_label'] = facilityFrame['project_location'].str.extract(r'\[(.*?)\]')  # 用正则表达式提取
	facilityFrame['region_label'] = facilityFrame['region_label'].str.split()  # 提取内容包含市辖区和区内小地区
	facilityFrame['region_name'] = facilityFrame['region_label'].str[1]  # 只需保留后者

	# 按照地区合并
	facilityFrame = pd.merge(facilityFrame, regionCopy, left_on = 'region_name', right_on = 'region_name', how = 'left')
	facilityFrame['facility_id'] = [None] * len(facilityFrame)  # 提前新开一列

	# 对配套进行编号
	for item in regionCopy['region_name']:  # region中的region_name已经进行了去重
		indices = facilityFrame.loc[facilityFrame['region_name'] == item].index.tolist()  # 列出当前地区下的所有配套
		number = 1  # 自增变量
		for idx in indices:  # 将f(即facility)和左侧补0的3位数字组成的4位编号追加到6位地区编号后，形成10位配套编号
			facilityFrame.loc[idx, 'facility_id'] = facilityFrame.loc[idx, 'region_id'] + 'f' + str(number).zfill(3)
			number += 1
	facilityFrame = facilityFrame[facilityFrame['facility_id'].notna()]  # 把没有获得地区编号的行删除

	return facilityFrame.drop(['project_location', 'city_name', 'region_name', 'region_id', 'region_label'],
							  axis = 1)  # 删除多余列


# 制作 Houses.csv
def house_csv(homeFrame, regionCopy):
	# 保留必要列，按楼盘名去重
	houseFrame = homeFrame.drop(['facility_type', 'facility_name', 'distance'], axis = 1). \
		drop_duplicates(subset = 'project_name')
	houseFrame['region_label'] = houseFrame['project_location'].str.extract(r'\[(.*?)\]')  # 用正则表达式提取
	houseFrame['region_label'] = houseFrame['region_label'].str.split()  # 提取内容包含市辖区和区内小地区
	houseFrame['region_name'] = houseFrame['region_label'].str[1]  # 只需保留后者

	# 提取地址
	houseFrame['house_address'] = houseFrame['project_location'].str.strip()
	houseFrame['house_address'] = houseFrame['house_address'].str.split(']')
	houseFrame['house_address'] = houseFrame['house_address'].str[1]
	houseFrame['house_address'] = houseFrame['house_address'].str.replace('\xa0', '')

	# 提取户型和面积
	numPattern, floorPattern, sizePattern = r'\d+', r'(\d+)室/(\d+)室', r'(\d+)-(\d+)㎡'
	houseFrame['floor_plan'] = houseFrame['floor_message'].apply(lambda x: re.search(floorPattern, x).groups() \
		if re.search(floorPattern, x) else None)  # 存储户型信息
	houseFrame['floor_plan'] = houseFrame['floor_plan'].fillna("('0', '0')")  # 没有户型信息
	houseFrame['floor_size'] = houseFrame['floor_message'].apply(lambda x: re.search(sizePattern, x).groups() \
		if re.search(sizePattern, x) else None)  # 存储面积信息
	houseFrame['floor_size'] = houseFrame['floor_size'].fillna("('0', '0')")  # 没有面积信息

	houseFrame = pd.merge(houseFrame, regionCopy, left_on = 'region_name', right_on = 'region_name', how = 'left')
	houseFrame['house_id'] = [None] * len(houseFrame)  # 提前新开一列

	# 对楼盘进行编号
	for item in regionCopy['region_name']:  # region中的region_name已经进行了去重
		indices = houseFrame.loc[houseFrame['region_name'] == item].index.tolist()  # 列出当前地区下的所有楼盘
		number = 1  # 自增变量
		for idx in indices:  # 将h(即house)和左侧补0的3位数字组成的4位编号追加到6位地区编号后，形成10位楼盘编号
			houseFrame.loc[idx, 'house_id'] = houseFrame.loc[idx, 'region_id'] + 'h' + str(number).zfill(3)
			number += 1
	houseFrame = houseFrame[houseFrame['house_id'].notna()]  # 把没有获得楼盘编号的行删除

	# 导出前微调
	houseFrame['average_price'] = pd.to_numeric(houseFrame['average_price'], errors = 'coerce').fillna(0).astype(int)
	houseFrame = houseFrame.rename({'project_name': 'house_name', 'project_link': 'house_link'}, axis = 1)
	return houseFrame.drop(['project_location', 'floor_message', 'region_label', 'region_name', 'region_id',
							'district_name', 'city_name'], axis = 1)


# 制作Distance.csv
def distance_csv(homeFrame, houseCopy, facilityCopy):
	distanceFrame = homeFrame[['project_name', 'facility_name', 'distance']].drop_duplicates(
		subset = ['project_name', 'facility_name'])  # 去除同一对楼盘和配套的重复行，保留第一次出现的行
	distanceFrame = distanceFrame.rename({'project_name': 'house_name'}, axis = 1)  # 改个名
	hCopy = houseCopy.loc[:, ['house_name', 'house_id']]
	fCopy = facilityCopy.loc[:, ['facility_name', 'facility_id']]

	# 合并
	distanceFrame = pd.merge(distanceFrame, hCopy, left_on = 'house_name', right_on = 'house_name', how = 'left')
	distanceFrame = pd.merge(distanceFrame, fCopy, left_on = 'facility_name', right_on = 'facility_name', how = 'left')
	distanceFrame = distanceFrame[distanceFrame['house_id'].notna()]
	distanceFrame = distanceFrame[distanceFrame['facility_id'].notna()]
	distanceFrame = distanceFrame[distanceFrame['distance'].notna()]

	# 导出前微调
	distanceFrame['distance'] = distanceFrame['distance'].str.extract('(\d+)').astype(int)
	return distanceFrame.drop(['house_name', 'facility_name'], axis = 1)

def output_csv(code):
	# 遍历DataFrame
	copies = './OriginalCopy'
	frames = os.listdir(copies)
	print(frames)

	if code == 1:
		# 导出Regions.csv
		district = pd.read_excel('./PureTable/District.xlsx')
		outputRegion = []
		for f in frames:
			mainFrame = pd.read_excel("{0}/{1}".format(copies, f))
			tmp = region_csv(mainFrame, district)
			# print(tmp.head(20))
			outputRegion.append(tmp)
		pd.concat(outputRegion).to_csv('./PureTable/Regions.csv', index = False)

	elif code == 2:
		# 导出Facilities.csv
		region = pd.read_csv('./PureTable/Regions.csv')
		outputFacility = []
		for f in frames:
			mainFrame = pd.read_excel("{0}/{1}".format(copies, f))
			tmp = facility_csv(mainFrame, region)
			# print(tmp.head(20))
			outputFacility.append(tmp)
		pd.concat(outputFacility).to_csv('./PureTable/Facilities.csv', index = False)

	elif code == 3:
		# 导出Houses.csv
		region = pd.read_csv('./PureTable/Regions.csv')
		outputHouse = []
		for f in frames:
			mainFrame = pd.read_excel("{0}/{1}".format(copies, f))
			tmp = house_csv(mainFrame, region)
			# print(tmp.head(20))
			outputHouse.append(tmp)
		pd.concat(outputHouse).to_csv('./PureTable/Houses.csv', index = False)

	elif code == 4:
		# 导出Distance.csv
		house = pd.read_csv('./PureTable/Houses.csv')
		facility = pd.read_csv('./PureTable/Facilities.csv')
		outputDistance = []
		for f in frames:
			mainFrame = pd.read_excel("{0}/{1}".format(copies, f))
			tmp = distance_csv(mainFrame, house, facility)
			print(tmp.head(20))
			outputDistance.append(tmp)
		pd.concat(outputDistance).to_csv('./PureTable/Distance.csv', index = False)


if __name__ == '__main__':
	output_csv(3)
