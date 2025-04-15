# Editor:CharPy

import pandas as pd
from py2neo import Graph, Node, Relationship

# 文件路径
updateRegion = '../Data/PureTable/Regions.csv'
updateFacility = '../Data/PureTable/Facilities.csv'
updateHouse = '../Data/PureTable/Houses.csv'
updateDistance = '../Data/PureTable/Distance.csv'
graph = Graph("http://localhost:7474", auth=("neo4j", "Pine20210238"))
def import_region_data():
	tx = graph.begin()  # 创建事务, 批量提交

	try:
		importRegion = pd.read_csv(updateRegion)
		for index, row in importRegion.iterrows():
			region = Node('Region',
						 region_id = row['region_id'],
						 region_name = row['region_name'],
						 district_name = row['district_name'],
						 city_name = row['city_name'])

			tx.create(region)

		graph.commit(tx)  # 提交剩余数据
		print(f"成功导入 {len(importRegion)} 条数据")

	except Exception as e:
		graph.rollback(tx)
		print("导入失败:", str(e))

def import_facility_data():
	tx = graph.begin()  # 创建事务, 批量提交

	try:
		importFacility = pd.read_csv(updateFacility)
		for index, row in importFacility.iterrows():
			region = Node('Facility',
						  facility_id = row['facility_id'],
						  facility_name = row['facility_name'],
						  facility_type = row['facility_type'])

			tx.create(region)

		graph.commit(tx)  # 提交数据
		print(f"成功导入 {len(importFacility)} 条数据")

	except Exception as e:
		graph.rollback(tx)
		print("导入失败:", str(e))

def import_house_data():
	tx = graph.begin()  # 创建事务, 批量提交

	try:
		importHouse = pd.read_csv(updateHouse)
		for index, row in importHouse.iterrows():
			house = Node('House',
						 house_id = row['house_id'],
						 house_name = row['house_name'],
						 house_address = row['house_address'],
						 floor_plan = row['floor_plan'],
						 floor_size = row['floor_size'],
						 average_price = row['average_price'],
						 house_link = row['house_link'])

			tx.create(house)

		graph.commit(tx)  # 提交数据
		print(f"成功导入 {len(importHouse)} 条数据")

	except Exception as e:
		graph.rollback(tx)
		print("导入失败:", str(e))

def import_distance_data():
	graph.run("CREATE INDEX house_id_index IF NOT EXISTS FOR (h:House) ON (h.house_id)")
	graph.run("CREATE INDEX facility_id_index IF NOT EXISTS FOR (f:Facility) ON (f.facility_id)")
	# 分批次处理（避免内存溢出）
	batch_size = 500
	total_processed = 0

	tx = graph.begin()
	try:
		importDistance = pd.read_csv(updateDistance)
		for index, row in importDistance.iterrows():
			houseMatch, facilityMatch = row['house_id'], row['facility_id']
			distance = int(row["distance"])  # 距离
			houseNode = graph.nodes.match("House", house_id = houseMatch).first()  # 查找 House 节点
			facilityNode = graph.nodes.match("Facility", facility_id = facilityMatch).first()  # 查找 Facility 节点

			# 若匹配失败
			if not houseNode:
				print(f"警告: 未能匹配到楼盘 {houseMatch}")
				continue
			if not facilityNode:
				print(f"警告: 未能匹配到配套 {facilityMatch}")
				continue

			# 创建关系
			rel_hf = Relationship(houseNode, "H_NEAR_F", facilityNode, distance = distance)
			if not graph.exists(rel_hf):
				tx.create(rel_hf)
			rel_fh = Relationship(facilityNode, "F_NEAR_H", houseNode, distance = distance)
			if not graph.exists(rel_fh):
				tx.create(rel_fh)

			if index % batch_size == 0:
				tx.commit()
				total_processed += batch_size
				print(f"已提交 {total_processed} 条关系")
				tx = graph.begin()  # 开启新事务

		graph.commit(tx)
		print(f"总计创建 {len(importDistance)} 条关系")

	except Exception as e:
		graph.rollback(tx)
		print(f"批量处理失败: {str(e)}")

def import_hr_data():
	# 创建索引以提升查询性能
	graph.run("CREATE INDEX region_id_index IF NOT EXISTS FOR (r:Region) ON (r.region_id)")
	graph.run("CREATE INDEX house_id_index IF NOT EXISTS FOR (h:House) ON (h.house_id)")

	# 分批次处理（避免内存溢出）
	batch_size = 500
	skip = 0
	total_processed = 0

	# 获取所有 House 节点
	query_house = """
	    MATCH (h:House)
	    WHERE size(h.house_id) >= 6
	    RETURN h.house_id AS house_id, h
	    SKIP $skip_count LIMIT $batch_size
	    """

	while True:
		# 查询当前批次的 House 节点
		houseBatch = graph.run(query_house, skip_count = skip, batch_size = batch_size).data()
		if not houseBatch:
			break

		tx = graph.begin()
		try:
			for record in houseBatch:
				houseMatch = record["house_id"]
				houseNode = record["h"]
				regionMatch = houseMatch[:6]  # 提取前6位

				# 查找对应的 Region 节点
				regionNode = graph.nodes.match("Region", region_id = regionMatch).first()

				if regionNode:
					# 创建关系
					rel_hr = Relationship(houseNode, "H_LOCATE_R", regionNode)
					if not graph.exists(rel_hr):
						tx.create(rel_hr)
					rel_rh = Relationship(regionNode, "R_INCLUDE_H", houseNode)
					if not graph.exists(rel_rh):
						tx.create(rel_rh)
				else:
					print(f"警告: {houseMatch} 无匹配 Region 节点")

			graph.commit(tx)
			total_processed += len(houseBatch)
			print(f"已处理 {total_processed} 条数据")
			skip += batch_size

		except Exception as e:
			graph.rollback(tx)
			print(f"批量处理失败: {str(e)}")
			break

def import_fr_data():
	# 创建索引以提升查询性能
	graph.run("CREATE INDEX region_id_index IF NOT EXISTS FOR (r:Region) ON (r.region_id)")
	graph.run("CREATE INDEX facility_id_index IF NOT EXISTS FOR (f:Facility) ON (f.facility_id)")

	# 分批次处理（避免内存溢出）
	batch_size = 500
	skip = 0
	total_processed = 0

	# 获取所有 Facility 节点
	query_facility = """
		    MATCH (f:Facility)
		    WHERE size(f.facility_id) >= 6
		    RETURN f.facility_id AS facility_id, f
		    SKIP $skip_count LIMIT $batch_size
		    """

	while True:
		# 查询当前批次的 Facility 节点
		facilityBatch = graph.run(query_facility, skip_count = skip, batch_size = batch_size).data()
		if not facilityBatch:
			break

		tx = graph.begin()
		try:
			for record in facilityBatch:
				facilityMatch = record["facility_id"]
				facilityNode = record["f"]
				regionMatch = facilityMatch[:6]  # 提取前6位

				# 查找对应的 Region 节点
				regionNode = graph.nodes.match("Region", region_id = regionMatch).first()

				if regionNode:
					# 创建关系
					rel_fr = Relationship(facilityNode, "F_LOCATE_R", regionNode)
					if not graph.exists(rel_fr):
						tx.create(rel_fr)
					rel_rf = Relationship(regionNode, "R_INCLUDE_F", facilityNode)
					if not graph.exists(rel_rf):
						tx.create(rel_rf)
				else:
					print(f"警告: {facilityMatch} 无匹配 Region 节点")

			graph.commit(tx)
			total_processed += len(facilityBatch)
			print(f"已处理 {total_processed} 条数据")
			skip += batch_size

		except Exception as e:
			graph.rollback(tx)
			# print(f"批量处理失败: {str(e)}")
			print(type(e))
			break

def import_data(code):
	if code == 1:
		import_region_data()
	elif code == 2:
		import_facility_data()
	elif code == 3:
		import_house_data()
	elif code == 4:
		import_distance_data()
	elif code == 5:
		import_hr_data()
	elif code == 6:
		import_fr_data()


if __name__ == '__main__':
	'''
	补充说明
	
	updateFacilityData.py中facility_name一项带有
	【中学】、【小学】、【幼儿园】字样的Facility实体，
	在neo4j中已经被去除了这些字样，通过以下cypher查询去除：
	
	MATCH (f:Facility)
	WHERE 
	  f.facility_name CONTAINS "【中学】" OR
	  f.facility_name CONTAINS "【幼儿园】" OR
	  f.facility_name CONTAINS "【小学】"
	WITH f,
	  REPLACE(f.facility_name, "【中学】", "") AS step1,
	  REPLACE(f.facility_name, "【幼儿园】", "") AS step2,
	  REPLACE(f.facility_name, "【小学】", "") AS step3
	SET f.facility_name = 
	  REPLACE(REPLACE(REPLACE(
		f.facility_name,
		"【中学】", ""),
		"【幼儿园】", ""),
		"【小学】", "")
	'''
	import_data(5)
