# Editor:CharPy
# Edit time:2025/4/7 12:09


from ClassifyQuestion import *
from ControlAction import *
from GoodTools import *

'''问答类'''
class Charlie:
    def __init__(self, prefix):

        self.default = '您好，我是购房决策小助手Charlie，前来为您答疑解惑，如我未能明白您的意思还请多多体谅~'
        self.default += '\n@ps: 输入“数据计算”可进入购房决策指标计算器，输入“需求评估”可进入房源评估程序'

        self.prefix = prefix
        self.tool = GoodTools(self.prefix, self.default)

        self.classifier = QuestionClassifier(self.default)
        self.controller = ActionController(self.tool)

    def chat_main(self, sent):
        res_classify = self.classifier.classifier_main(sent)
        if not res_classify:
            return self.default

        return self.controller.controller_main(res_classify, self.default)


if __name__ == '__main__':
    handler = Charlie('Charlie:')
    while 1:
        question = input('User:')
        answer = handler.chat_main(question)
        handler.tool.print_prefix(answer)
