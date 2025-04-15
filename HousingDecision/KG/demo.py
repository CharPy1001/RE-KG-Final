# Editor:CharPy
# Edit time:2025/4/7 18:09

# from ClassifyQuestion
# # 问句疑问词
# self.confirm_qwds = ['有无', '是否', '能否', '能不能', '有没有', '没有', '是不是', '还是']
# self.exist_qwds = ['有', '属于', '包括', '内有', '包含', '带有', '具有', '存在', '含有', '还有', '都有', '哪里', '哪些', '哪家', '哪位', '哪边']
# self.amount_qwds = ['多少', '多大', '多久', '几', '不超过', '不低于', '多贵', '多便宜', '多高', '多低', '多长',
# 					'左右', '上下', '以内', '以下', '以外', '以上', '多少次', '多少钱', '多少元', '多少万', '多少平米',
# 					'达到', '低至', '高达', '多少年', '多少个月', '多少天', '多少个', '几个', '几米', '几平米',
# 					'多少月', '多少天', '多远', '多近', '多少米', '范围内', '时间内', '多少期']


ipo = ['深圳', '广州', '佛山', '北京', '烤鸭']
dictDemo = {'深圳': 'sz', '广州': 'gz', '佛山': 'fs'}

def shit(numbers):
    n = len(numbers)
    matrix = [[0.0] * n for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 1.0  # 对角线元素为1
            else:
                # 处理除以0的情况（可选，根据需求调整）
                matrix[i][j] = numbers[i] / numbers[j]
    return matrix

print(shit([1, 3, 5]))

# set1 = {1, 2, 3, 4}
# set2 = {3, 4, 5, 6}
#
# intersection = set1 & set2
# print(intersection)  # 输出: {3, 4}
# print("7800000"[1:7])

# try:
#     res = shit(int)
#     print(res, type(res))
#
# except Exception as e:
#     print(str(e), type(e))


