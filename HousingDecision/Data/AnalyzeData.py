# Editor:CharPy
# Edit time:2025/4/10 8:26

""" 看均价范围
MATCH (h:House)
WHERE h.average_price <> 0
RETURN h.average_price
ORDER BY h.average_price ASC
"""

""" 看平均总价区间
MATCH (h:House)
WHERE h.price > 0  // 过滤无效价格
WITH 
  h,
  // 计算区间下限（单位：百万）
  FLOOR(h.price / 1) AS interval_start 
WITH 
  // 构建区间字符串（如 "1-2百万"）
  interval_start + "-" + (interval_start + 1) + "百万" AS price_range,
  h
RETURN 
  price_range AS 价格区间,
  COUNT(h) AS 房屋数量
ORDER BY interval_start ASC
"""

"""
MATCH (house:House)
WITH house, 
	 SPLIT(SUBSTRING(house.floor_size, 1, SIZE(house.floor_size)-2), ', ') AS parts
WITH house, 
	 toInteger(substring(parts[0], 1, size(parts[0])-2)) AS x, 
	 toInteger(substring(parts[1], 1, size(parts[1])-2)) AS y
WHERE house.average_price > 0 AND x > 0 AND y > 0
WITH house, 
	 house.average_price * x AS price_min, 
	 house.average_price * y AS price_max
WITH house, price_min, price_max,
	 (price_min + price_max) / 2 AS ap
WITH house, ap,
  // 计算区间下限（单位：百万）
  FLOOR(ap / 1000000) AS interval_start 
WITH house, interval_start,
  interval_start + "-" + (interval_start + 1) AS price_range
ORDER BY interval_start ASC
RETURN 
  price_range AS 价格区间,
  COUNT(house) AS 房屋数量
"""

"""
		lpr = round(lpr/12, 4)
		dr *= 12
		common = (1+lpr) ** dr
		month_payment = m * payroll
		if mode == 1:  # 等额本息方式，总利息相比等额本金较高
			principal = m * payroll * ((1+lpr) ** dr - 1) / (lpr * (1+lpr) ** dr)
			total = m * payroll * dr
			return {'principal': principal, 'interest': total - principal,
					'total': total}
		elif mode == 2:  # 等额本金方式，总利息相比等额本息较低
			principal = m * payroll / (lpr + 1 / dr)
			interest = (m * payroll * lpr * (dr + 1)) / (2 * (1 / dr + lpr))
			return {'principal': principal, 'interest': interest,
					'total': principal + interest}
"""

'''
演示问题
**非结构化问题**
1、保利新汇城在哪个区
2、前海壹方汇位于哪个城市
3、金地峰境誉府附近有什么配套
4、旭辉清樾的交通情况
5、华润置地天河润府附近有哪些商场（二次兜底）
6、太平洋国际周围有没有医院
7、盛璟润府周边有什么学校
8、哪些中学在狮山锦绣半岛附近
9、南驰都湖国际的小学分布
10、找一下顺德悦府附近的幼儿园
11、帮我瞅瞅深圳的房子
12、介绍一下禅城的基础设施
13、给我看看芳村的房屋均价
14、碧桂园有哪些楼盘
15、五矿万境水岸
16、天河
17、蛇口
18、佛山
19、广东实验中学
20、东秀小学
21、沙嘴幼儿园
22、深圳华侨城医院
23、嘉意台
24、沙步大道
'''
