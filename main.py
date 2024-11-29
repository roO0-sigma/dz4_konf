import struct
import sys
import json
from math import sqrt

def assemble(input_file, binary_file, log_file):
    instructions = [] # список иснтрукций, переведённых в байт-код
    log_entries = [] # список кортежей для записи в лог-файл

    with open(input_file, 'r') as f:
        for line in f:
            parts = line.strip().split() # разделение прочитанной команды на части
            if not parts:
                continue
            if len(parts) == 1:
                A = int(parts[0])
            else:
                A, B = map(int, parts)  # получение значений аргументов и перевод их в int числа
            if A == 90: # обработка загрузки константы
                instruction = struct.pack('>B5s', A, struct.pack('>H', B) + bytes(3))
                instructions.append(instruction) # добавление инструкции в список для хранения инструкций
                log_entries.append(('LOAD_CONST', A, B)) # добавление кортежа аргументов инструкции для лог-файла

            elif A == 1: # обработа чтения из памяти
                instruction = struct.pack('>B5s', A, struct.pack('>B', B) + bytes(4))
                instructions.append(instruction)
                log_entries.append(('READ_MEM', A, B))

            elif A == 62:  # обработка записи в память
                instruction = struct.pack('>B5s', A, bytes(5))
                instructions.append(instruction)
                log_entries.append(('WRITE_MEM', A))

            elif A == 137: # обработка операции sqrt()
                instruction = struct.pack('>B5s', A, struct.pack('>B', B) + bytes(4))
                instructions.append(instruction)
                log_entries.append(('SQRT', A, B))
            else:
                print('Invalid command format')
                continue

        # запись байт кода в бинарный файл
        with open(binary_file, 'wb') as bin_file:
            for instruction in instructions:
                bin_file.write(instruction)

        # формирование лог-файла в формате JSON
        log_dict = []  # создаем список для хранения лог-записей
        for entry in log_entries:
            if len(entry) == 3:
                log_dict.append({
                    "key": entry[0],
                    "A": entry[1],
                    "B": entry[2],
                })
            else:
                log_dict.append({
                    "key": entry[0],
                    "A": entry[1],
                })
        with open(log_file, 'w') as log_f:
            json.dump(log_dict, log_f, indent=4)  # запись в лог-файл

# класс для реализации стека
class Stack:
    def __init__(self):
        self.values = []
    def push(self, i):
        self.values.append(i)
    def peek(self):
        return self.values[-1]
    def pop(self):
        value = self.values[-1]
        self.values = self.values[:-1]
        return value

class VirtualMachine:
    def __init__(self, memory_size=1024):
        self.memory = [0] * memory_size  # инициализация памяти
        self.stack = Stack() # инициализация стека

        self.pc = 0  # программный счетчик
    def load_program(self, binary_file):
        with open(binary_file, 'rb') as f:
            self.program = f.read()  # загрузка программы в память

    def execute(self, result_range_start, result_range_end):

        while self.pc < len(self.program):
            # чтение 1 байта - кода операции
            opcode = self.program[self.pc]

            if opcode == 0x5A:  # LOAD_CONST
                instruction = self.program[self.pc:self.pc + 6]  # чтение 6 байт
                A = instruction[0]
                B = struct.unpack('>H', instruction[1:3])[0]
                self.stack.push(B) # записываем константы в стек
                self.pc += 6

            elif opcode == 0x01:  # READ_MEM
                instruction = self.program[self.pc:self.pc + 6]  # чтение 6 байт
                A = instruction[0]
                B = instruction[1]
                self.stack.push(self.memory[self.stack.pop() + B]) # запись в стек
                self.pc += 6

            elif opcode == 0x3E:  # WRITE_MEM
                instruction = self.program[self.pc:self.pc + 6]  # чтение 6 байт
                A = instruction[0]
                operand = self.stack.pop()
                addres = self.stack.pop()
                self.memory[addres] = operand # запись значения в память по адресу, полученному из стека
                self.pc += 6

            elif opcode == 0x89:  # SQRT
                instruction = self.program[self.pc:self.pc + 6]  # чтение 6 байт
                A = instruction[0]
                B = instruction[1]
                operand = self.memory[self.stack.pop()]
                self.memory[self.stack.pop() + B] = sqrt(operand) # запись в память корня операнда
                self.pc += 6

            else:
                print(f"Unknown opcode: {opcode}")  # сообщение о неизвестном коде операции
                break

        return self.memory[result_range_start:result_range_end + 1] # возврат участка памяти, содержащего результат

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python assembler_interpreter.py <input_file> <binary_file> <log_file> <result_range_start> <result_range_end>")
        sys.exit(1)

    # получение аргументов из командной строки
    input_file = sys.argv[1] # путь к обрабатываемому файлу
    binary_file = sys.argv[2] # путь к бинарному файлу для записи результата работы ассемблера
    log_file = sys.argv[3] # путь к лог-файлу
    result_range_start = int(sys.argv[4]) # начало участка памяти, хранящего результат
    result_range_end = int(sys.argv[5]) # конец участка памяти, хранящего результат

    assemble(input_file, binary_file, log_file) # ассемблирование команд

    vm = VirtualMachine()
    vm.load_program(binary_file) # загрузка ассемблированных команд в память УВМ
    results = vm.execute(result_range_start, result_range_end) # интерпретация команд

    # запись результатов в json файл
    results_dict = {"memory_units": []}
    count = int(result_range_start)

    for i in range(len(results)):
        results_dict["memory_units"].append({"unit": count, "value": results[i]})
        count += 1

    with open("results.json", 'w') as res_f:
        json.dump(results_dict, res_f, indent=4)

