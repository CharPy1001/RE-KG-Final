# Editor:CharPy

from GoodTools import *

class QuestionParser:

    def __init__(self, tool):
        self.tool = tool
        self.locationDict = self.tool.use_locDict()

    '''构建实体节点'''
    def build_entitydict(self, args):
        entity_dict = {}
        for arg, types in args.items():
            for t in types:
                if t not in entity_dict:
                    entity_dict[t] = [arg]
                else:
                    entity_dict[t].append(arg)

        return entity_dict

    '''解析主函数'''
    def parser_main(self, res_classify):
        args = res_classify['args']
        entity_dict = self.build_entitydict(args)
        question_types = res_classify['question_types']
        outputSqls = []

        for question_type in question_types:
            demandSql = dict()
            demandSql['question_type'] = question_type
            sql = []

            check_house = ['house_location', 'house_facility',
                           'house_business', 'house_traffic',
                           'house_hospital', 'house_school',
                           'house_primarySchool', 'house_information',
                           'house_kindergarten', 'house_middleSchool']
            check_location = ['location_house', 'location_facility', 'location_price']
            check_facility = ['facility_location', 'facility_house']

            if question_type in check_house:
                sql = self.sql_transfer(question_type, entity_dict.get('house'))

            elif question_type in check_facility:
                sql = self.sql_transfer(question_type, entity_dict.get('facility'))

            elif question_type in check_location:
                sql = self.sql_transfer(question_type, entity_dict.get('location'))

            elif question_type == 'developer_house':
                sql = self.sql_transfer(question_type, entity_dict.get('developer'))

            if sql:
                demandSql['sql'] = sql
                outputSqls.append(demandSql)

        return outputSqls

    '''针对不同的问题，分开进行处理'''
    def sql_transfer(self, question_type, entities):
        if not entities:
            return []

        duplicateEntities = entities.copy()
        replace_code = "{0}"
        phrase = "{0}"

        # 已知房源名字，求其所在城市/辖区/地区
        if question_type == 'house_location':
            phrase = """
            MATCH (h:House {house_name: "{0}"})
            WITH h,
              LEFT(h.house_id, 2)  AS cityCode,    
              LEFT(h.house_id, 4)  AS districtCode
            MATCH (r:Region {region_id: LEFT(h.house_id, 6)})
            RETURN 
              h.house_name AS houseName,
              h.house_address AS houseAddress,
              cityCode     AS cityID,
              districtCode AS districtID,
              r.region_name AS regionName
            """

        # 已知配套名字，求其所在城市/辖区/地区
        elif question_type == 'facility_location':
            phrase = """
            MATCH (f:Facility {facility_name: "{0}"})
            WITH f,
              LEFT(f.facility_id, 2)  AS cityCode,    
              LEFT(f.facility_id, 4)  AS districtCode
            MATCH (r:Region {region_id: LEFT(f.facility_id, 6)})
            RETURN 
              f.facility_name AS facilityName,
              f.facility_type AS facilityType,
              cityCode     AS cityID,
              districtCode AS districtID,
              r.region_name AS regionName
            """

        # 已知房源名字，求其配套
        elif question_type == 'house_facility':
            phrase = """
            MATCH (h:House {house_name: "{0}"})-[r:H_NEAR_F]->(f:Facility)
            WHERE f.facility_type IN ["教育", "医疗", "商业", "交通"]
            WITH h, f,
              f.facility_type AS type, 
              f.facility_name AS name, 
              r.distance AS distance
            ORDER BY type, distance ASC 
            
            WITH 
              h.house_name AS houseName,
              type, 
              collect({name: name, distance: distance})[0..3] AS top3
            UNWIND top3 AS entry
            RETURN 
              houseName,
              type AS facilityType,
              entry.name AS facilityName,
              entry.distance AS distance
            ORDER BY facilityType, distance
            """

        # 已知房源名字，求其商业配套
        elif question_type == 'house_business':
            phrase = """
            MATCH (h:House {house_name: "{0}"})-[r:H_NEAR_F]->(f:Facility)
            WHERE f.facility_type = "商业"
            WITH f, r.distance AS distance, h
            ORDER BY distance ASC
            RETURN f.facility_name AS facilityName, distance, h.house_name AS houseName
            LIMIT 3
            """

        # 已知房源名字，求其交通配套
        elif question_type == 'house_traffic':
            phrase = """
            MATCH (h:House {house_name: "{0}"})-[r:H_NEAR_F]->(f:Facility)
            WHERE f.facility_type = "交通"
            WITH f, r.distance AS distance, h
            ORDER BY distance ASC
            RETURN f.facility_name AS facilityName, distance, h.house_name AS houseName
            LIMIT 3
            """

        # 已知房源名字，求其医疗配套
        elif question_type == 'house_hospital':
            phrase = """
            MATCH (h:House {house_name: "{0}"})-[r:H_NEAR_F]->(f:Facility)
            WHERE f.facility_type = "医疗"
            WITH f, r.distance AS distance, h
            ORDER BY distance ASC
            RETURN f.facility_name AS facilityName, distance, h.house_name AS houseName
            LIMIT 3
            """

        # 已知房源名字，求其教育配套
        elif question_type == 'house_school':
            phrase = """
            MATCH (h:House {house_name: "{0}"})-[r:H_NEAR_F]->(f:Facility)
            WHERE f.facility_type = "教育"
            WITH f, r.distance AS distance, h
            ORDER BY distance ASC
            RETURN f.facility_name AS facilityName, distance, h.house_name AS houseName
            LIMIT 3
            """

        # 已知房源名字，求附近的小学
        elif question_type == 'house_primarySchool':
            phrase = """
            MATCH (h:House {house_name: "{0}"})-[r:H_NEAR_F]->(f:Facility)
            WHERE f.facility_name CONTAINS "小学"
            WITH f, r.distance AS distance, h
            ORDER BY distance ASC
            RETURN f.facility_name AS facilityName, distance, h.house_name AS houseName
            LIMIT 3
            """

        # 已知房源名字，求附近的中学
        elif question_type == 'house_middleSchool':
            phrase = """
            MATCH (h:House {house_name: "{0}"})-[r:H_NEAR_F]->(f:Facility)
            WHERE f.facility_name CONTAINS "中学"
            WITH f, r.distance AS distance, h
            ORDER BY distance ASC
            RETURN f.facility_name AS facilityName, distance, h.house_name AS houseName
            LIMIT 3
            """

        # 已知房源名字，求附近的幼儿园
        elif question_type == 'house_kindergarten':
            phrase = """
            MATCH (h:House {house_name: "{0}"})-[r:H_NEAR_F]->(f:Facility)
            WHERE f.facility_name CONTAINS "幼"
            WITH f, r.distance AS distance, h
            ORDER BY distance ASC
            RETURN f.facility_name AS facilityName, distance, h.house_name AS houseName
            LIMIT 3
            """

        # 已知配套名字，求其所在房源
        elif question_type == 'facility_house':
            phrase = """
            MATCH (f:Facility)-[:F_NEAR_H]->(h:House)
            WHERE f.facility_name = "{0}"
            RETURN h.house_name AS houseName,
                h.house_address AS houseAddress,
                h.average_price AS averagePrice,
                h.floor_plan AS floorPlan,
                h.floor_size AS floorSize,
                h.house_link AS houseLink,
                f.facility_name AS facilityName,
                f.facility_type AS facilityType
            """

        # 已知城市/辖区/地区，求其房源
        elif question_type == 'location_house':
            # 替换为ID
            tmp = []
            for ent in duplicateEntities:
                tmp.append(ent in self.locationDict.keys())
            for i in range(len(tmp)):
                if tmp[i]:
                    duplicateEntities[i] = self.locationDict[duplicateEntities[i]]

            phrase = """
            MATCH (h:House)
            WHERE h.house_id STARTS WITH "{0}"
            WITH h
            ORDER BY h.average_price ASC
            LIMIT 3
            RETURN h.house_name AS houseName,
                h.house_address AS houseAddress,
                h.average_price AS averagePrice,
                h.floor_plan AS floorPlan,
                h.floor_size AS floorSize,
                h.house_link AS houseLink,
                "{0}" AS locationID
            """

        # 已知城市/辖区/地区，求其配套
        elif question_type == 'location_facility':
            # 替换为ID
            tmp = []
            for ent in duplicateEntities:
                tmp.append(ent in self.locationDict.keys())
            for i in range(len(tmp)):
                if tmp[i]:
                    duplicateEntities[i] = self.locationDict[duplicateEntities[i]]

            phrase = """
            MATCH (f:Facility)
            WHERE
              f.facility_id STARTS WITH "{0}"
              AND f.facility_type IN ["教育", "医疗", "交通", "商业"]
            WITH 
              f.facility_type AS type, 
              f.facility_name AS name
            ORDER BY type, rand()
            WITH type, collect(name)[0..3] AS sampledNames
            UNWIND sampledNames AS facilityName
            RETURN 
              type AS facilityType,
              facilityName,
              "{0}" AS locationID
            ORDER BY 
              CASE type
                WHEN "教育" THEN 1
                WHEN "医疗" THEN 2
                WHEN "交通" THEN 3
                WHEN "商业" THEN 4
              END
            """

        elif question_type == 'location_price':
            # 替换为ID
            tmp = []
            for ent in duplicateEntities:
                tmp.append(ent in self.locationDict.keys())
            for i in range(len(tmp)):
                if tmp[i]:
                    duplicateEntities[i] = self.locationDict[duplicateEntities[i]]

            phrase = """
            MATCH (h:House)
            WHERE h.house_id STARTS WITH "{0}"
            RETURN "{0}" AS locationID,
                toInteger(AVG(h.average_price)) AS avgPrice
            """

        # 已知开发商名字，求房源
        elif question_type == 'developer_house':
            phrase = """
            MATCH (h:House)
            WHERE h.house_name CONTAINS "{0}"
            WITH h
            ORDER BY rand()
            MATCH (r:Region {region_id: LEFT(h.house_id, 6)})
            RETURN h.house_name AS houseName,
                h.house_address AS houseAddress,
                h.average_price AS averagePrice,
                h.floor_plan AS floorPlan,
                h.floor_size AS floorSize,
                h.house_link AS houseLink,
                LEFT(h.house_id, 2) AS cityID,
                LEFT(h.house_id, 4) AS districtID,
                r.region_name AS regionName,
                "{0}" AS devName
            LIMIT 3
            """

        # 房源提问兜底，调取全面调取该房源信息
        elif question_type == 'house_information':
            phrase = """
            MATCH (h:House)
            WHERE h.house_name CONTAINS "{0}"
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
            """

        sql = [phrase.replace(replace_code, ent) for ent in duplicateEntities]
        return sql


if __name__ == '__main__':
    gt = GoodTools("Prefix:", "Default Message")
    handler = QuestionParser(gt)
