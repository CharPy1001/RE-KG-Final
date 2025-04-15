# Editor:CharPy
# Edit time:2025/4/7 18:13

from ParseQuestion import *
from SearchAnswer import *
from EvaluateNeeds import *
from CalculateFigure import *

class ActionController:
	def __init__(self, tool):
		self.parser = QuestionParser(tool)
		self.searcher = AnswerSearcher(tool)
		self.calculator = FigureCaculator(tool)
		self.evaluator = NeedsEvaluator(tool)

	def controller_main(self, res_classify, default_answer):
		question_types = res_classify['question_types']
		result = ""
		
		if 'calculation' in question_types:
			final_answers = self.calculator.calculator_main()
			if final_answers != 'exit':
				result += ("已为您返回以下计算结果" + final_answers)
			result += "\n您已退出计算器，可以继续向我提问"
		elif 'evaluation' in question_types:
			final_answers = self.evaluator.evaluator_main()
			result += ("已为您返回以下评估结果" + final_answers)
			result += "\n您已退出评估程序，可以继续向我提问"
		else:
			res_sql = self.parser.parser_main(res_classify)
			final_answers = self.searcher.search_main(res_sql)
			result += ("已为您返回{0}条信息\n".format(len(final_answers)) + "\n".join(final_answers))

		return result if final_answers else default_answer


if __name__ == '__main__':
	pass
