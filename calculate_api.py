from flask import Flask, request, jsonify
import re
import threading

app = Flask(__name__)

class Calculator:
    @staticmethod
    def tokenize(expression):
        token_pattern = r'\d+\.\d+|\d+|[+\-*/()]'
        tokens = re.findall(token_pattern, expression)

        processed_tokens = []
        unary_minus_stack = []

        for i, token in enumerate(tokens):
            if token == '-' and i > 0 and tokens[i - 1] == '-':
                processed_tokens.pop()
                processed_tokens.append('+')
            elif token == '-' and (i == 0 or tokens[i - 1] in '+*/('):
                processed_tokens.extend(['(', '0', '-'])
                unary_minus_stack.append(len(processed_tokens) - 1)
            else:
                processed_tokens.append(token)

        for pos in reversed(unary_minus_stack):
            processed_tokens.insert(pos + 2, ')')

        return processed_tokens

    @staticmethod
    def shunting_yard_algorithm(tokens):
        output = []
        operators = []
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
        open_parentheses = 0

        for token in tokens:
            if token.isnumeric() or token.replace('.', '', 1).isdigit():
                output.append(token)
            elif token == '(':
                operators.append(token)
                open_parentheses += 1
            elif token == ')':
                open_parentheses -= 1
                if open_parentheses < 0:
                    raise ValueError("Лишняя закрывающая скобка")
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                operators.pop()
            else:
                while operators and operators[-1] in precedence and precedence[operators[-1]] >= precedence[token]:
                    output.append(operators.pop())
                operators.append(token)

        while operators:
            op = operators.pop()
            if op == '(':
                raise ValueError("Незакрытая открывающая скобка")
            output.append(op)

        if open_parentheses > 0:
            raise ValueError("Незакрытые скобки в выражении")

        return output

    @staticmethod
    def evaluate_rpn(rpn):
        stack = []

        for token in rpn:
            if token.replace('.', '', 1).isdigit():
                stack.append(float(token))
            else:
                if len(stack) < 2:
                    raise ValueError("Неверное выражение в ОПН: недостаточно операндов(скорее всего вы забыли добавить какое-то число в свое выражение или сделали пробел между дробным числом)")

                b = stack.pop()
                a = stack.pop()

                if token == '+':
                    result = a + b
                elif token == '-':
                    result = a - b
                elif token == '*':
                    result = a * b
                elif token == '/':
                    if b == 0:
                        raise ZeroDivisionError("Ошибка: деление на ноль")
                    result = a / b
                else:
                    raise ValueError(f"Неверный оператор: {token}")

                stack.append(result)

        if len(stack) != 1:
            raise ValueError("Неверное выражение в ОПН: слишком много операндов(скорее всего вы поставили лишние числа в в свое выражение или сделали пробел между дробным числом)")

        return stack[0]

    @staticmethod
    def calculate(expression):
        try:
            tokens = Calculator.tokenize(expression)
            rpn = Calculator.shunting_yard_algorithm(tokens)
            return Calculator.evaluate_rpn(rpn)
        except ZeroDivisionError:
            return "Ошибка: деление на ноль."
        except ValueError as e:
            return f"Ошибка в выражении: {e}"
        except Exception as e:
            return f"Неизвестная ошибка: {e}"

# calculator = Calculator()

@app.route('/calculate', methods=['POST'])
def calculate_expression():
    data = request.get_json()
    expression = data.get("expression")
    if expression is None:
        return jsonify({"error": "No expression provided"}), 400
    try:
        result = Calculator.calculate(expression)
        return jsonify({"result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
    #app.run(debug=True)

if __name__ == '__main__':
    app_thread = threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5000})
    app_thread.start()

    while True:
        expression = input("Введите выражение (или 'exit' для выхода): ")
        if expression == 'exit':
            break
        result = Calculator.calculate(expression)
        print(result)