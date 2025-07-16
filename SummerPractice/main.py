import csv

types = []  # Создаём пустой список для хранения значений типа 'type'

with open('classified_tls.csv', 'r', encoding='utf-8') as file:
    reader = csv.reader(file)

    # Пропускаем первые 3 строки (заголовки)
    for _ in range(3):
        next(reader)

# Обрабатываем оставшиеся строки
    for row in reader:
        if len(row) >= 4:  # Проверяем, что строка содержит достаточно столбцов
            type_value = row[3].strip()  # Извлекаем и очищаем от пробелов
            if type_value:  # Если значение не пустое
                try:
                    num_value = int(type_value)  # Конвертируем строку в число
                    types.append(num_value)
                except ValueError:
                    print(f"Ошибка: значение '{type_value}' не может быть преобразовано в число")

# Выводим результат
print("types =",types)


def median_filter(sequence, window_size=9):
    smoothed = []
    n = len(sequence)
    for i in range(n):
        start = max(0, i - window_size // 2)
        end = min(n, i + window_size // 2 + 1)
        window = sequence[start:end]
        median = sorted(window)[len(window) // 2]
        smoothed.append(median)
    return smoothed


smoothed_median = median_filter(types, window_size=9)
print("smoothed_median =", smoothed_median)