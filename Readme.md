# Itmo-csa-lab4
- Черемисова Мария P3210
- Вариант `lisp | acc | harv | mc | tick | binary | stream | port | pstr | prob2 | cache`
  - `lisp`: Синтаксис языка Lisp. S-exp:
    1. Поддержка рекурсивных функций.
    2. Любое выражение (statement) - expression.
  - `acc` : Система команд должна быть выстроена вокруг аккумулятора:
    1. Инструкции - изменяют значение, хранимое в аккумуляторе.
    2. Ввод-вывод осуществляется через аккумулятор.
  - `harv` : Гарвардская архитектура.
  - `mc` : Команды реализованы с помощью микрокоманд.
  - `tick` : Процессор необходимо моделировать с точностью до такта, процесс моделирования может быть приостановлен на любом такте.
  - `binary` : Бинарное представление машинного кода.
  - `stream` : Ввод-вывод осуществляется как поток токенов.
  - `port` : Port-mapped (специальные инструкции для ввода-вывода), да я портовая шлюха.
  - `pstr` : Length-prefixed (Pascal string).
  - `prob2` : Euler problem 6 [link](https://projecteuler.net/problem=6).
  - `cache` : Работа с памятью реализуется через кеш.
    - Скорость доступа к кешу - 1 такт, к памяти - 10 тактов.

# Язак lisp
Основн на S-выражениях, где весь код представляется так: каждая конструкция записывается в виде списка, заключённого в круглые скобки, где первым элементом обычно является оператор или имя функции, а далее следуют аргументы. Ниже представлена формальная грамматика (в стиле BNF) языка, основанного на Lisp, определяющая допустимые конструкции программ.
```
<program> ::= <statement_list>

<statement_list> ::= <statement> | <statement> <statement_list>

<statement> ::= <var_declaration>
              | <if_statement>
              | <defunc_declaration>
              | <while_statement>
              | <function_call>
              | <print_string>
              | <read_line>

<var_declaration> ::= "(var" <identifier> <expression> ")"

<if_statement> ::= "(if" <condition> <statement_list> <statement_list> ")"

<while_statement> ::= "(while" <condition> <statement_list> ")"

<defunc_declaration> ::= "(defunc" <identifier> "(" <parameter_list> ")" <statement_list> ")"

<function_call> ::= "(funcall" <identifier> "(" <argument_list> "))"

<print_string> ::= "(print_string" <string> ")"

<read_line> ::= "(read_line" <identifier> ")"

<condition> ::= "(" <comparison_operator> <expression> <expression> ")"

<comparison_operator> ::= ">" | "<" | "="

<expression> ::= <number>
              | <identifier>
              | "(" <operator> <expression> <expression> ")"

<operator> ::= "+" | "-" | "*" | "/"

<parameter_list> ::= <identifier> | <identifier> <parameter_list>

<argument_list> ::= <expression> | <expression> <argument_list>

<identifier> ::= <letter> | <letter> <identifier_tail>

<identifier_tail> ::= <letter> | <digit> | <identifier_tail>

<string> ::= "\"" <string_content> "\""

<string_content> ::= <character> | <character> <string_content>

<character> ::= <letter> | <digit> | " " | "," | "!" | "?" 

<letter> ::= "a" | "b" | ... | "z" | "A" | "B" | ... | "Z"

<digit> ::= "0" | "1" | ... | "9"

<number> ::= <digit> | <digit> <number>

```
