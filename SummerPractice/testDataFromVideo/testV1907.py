import csv
from collections import defaultdict
import matplotlib.pyplot as plt
from datetime import datetime


class TrafficLightAnalyzer:
    def __init__(self, delta_t=5.0, confidence_threshold=70.0):
        self.delta_t = delta_t
        self.confidence_threshold = confidence_threshold
        self.data_main = defaultdict(list)
        self.data_left = defaultdict(list)
        self.data_right = defaultdict(list)

        self.color_priority = {
            '0': 0, 'unknown': 0,
            '1': 1, 'red': 1,
            '3': 3, 'yellow': 3,
            '2': 2, 'green': 2,
            '4': 4, 'left': 4,
            '5': 5, 'right': 5,
            '6': 6, 'up': 6,
            '7': 7, 'down': 7
        }

        self.color_names = {
            0: 'unknown',
            1: 'red',
            2: 'green',
            3: 'yellow',
            4: 'left',
            5: 'right',
            6: 'up',
            7: 'down'
        }

        self.status_types = {
            8: 'solid',
            9: 'flashing'
        }

    def load_data(self, filename):
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for _ in range(2):
                next(reader)

            for row in reader:
                try:
                    unix_time = float(row[0])
                    camera = row[2]

                    # Основной сигнал
                    main_color = self.color_priority.get(str(row[3]).lower(), 0)
                    main_status = int(row[4]) if len(row) > 4 and row[4] else 8
                    main_conf = float(row[5])
                    self.data_main[camera].append((unix_time, main_color,main_status, main_conf))

                    # Левая секция
                    left_color = self.color_priority.get(str(row[11]).lower(), 0) if len(row) > 11 and row[11] else 0
                    left_status = int(row[12]) if len(row) > 12 and row[12] else 8
                    left_conf = float(row[13]) if len(row) > 13 and row[13] else 0
                    if left_color != 0 or left_conf != 0:  # Только если есть данные
                        self.data_left[camera].append((unix_time, left_color,left_status, left_conf))

                    # Правая секция
                    right_color = self.color_priority.get(str(row[7]).lower(), 0) if len(row) > 7 and row[7] else 0
                    right_status = int(row[8]) if len(row) > 8 and row[8] else 8
                    right_conf = float(row[9]) if len(row) > 9 and row[9] else 0
                    if right_color != 0 or right_conf != 0:  # Только если есть данные
                        self.data_right[camera].append((unix_time, right_color,right_status, right_conf))

                except (IndexError, ValueError) as e:
                    print(f"Ошибка обработки строки: {row}. Ошибка: {e}")
                    continue

    def get_color_at_time(self, t, data_source):
        window = []
        flashing_colors = set()

        for camera, observations in data_source.items():
            for obs in observations:
                time, color, status,  confidence = obs
                if abs(time - t) <= self.delta_t / 2 and confidence >= self.confidence_threshold:
                    if status == 9:
                        flashing_colors.add(color)
                    window.append((color, confidence))

        if not window:
            return 0

        # Приоритет для мигающих сигналов
        if flashing_colors:
            # Выбираем самый приоритетный мигающий сигнал
            flashing_priority = {
                1: 3,  # Красный - высший приоритет
                3: 2,  # Желтый
                2: 1,  # Зеленый
                4: 1,  # Стрелки
                5: 1,
                6: 1
            }
            # Находим мигающий цвет с максимальным приоритетом
            flashing_color = max(flashing_colors, key=lambda x: flashing_priority.get(x, 0))
            return flashing_color

        # Обычная обработка для SOLID сигналов
        color_scores = defaultdict(float)
        for color, confidence in window:
            color_scores[color] += confidence

        if 0 in color_scores and len(color_scores) > 1:
            del color_scores[0]

        if not color_scores:
            return 0

        return max(color_scores.items(), key=lambda x: x[1])[0]

    def plot_single_signal(self, times, colors, color_map, title, ylabel):
        plt.figure(figsize=(9, 5))

        # Отображение исходных точек
        for camera, observations in color_map['data'].items():
            cam_times = [obs[0] for obs in observations]
            cam_colors = [obs[1] for obs in observations]
            plt.scatter(cam_times, cam_colors, alpha=0.3, label=f'Камера {camera} (raw)', s=30)


        # Сглаженная линия
        plt.plot(times, colors, 'k-', linewidth=2, label='Сглаженный сигнал')

        # Настройки графика
        plt.yticks(list(color_map['ticks'].keys()),
                   list(color_map['ticks'].values()))
        plt.xlabel('Время (Unix)')
        plt.ylabel(ylabel)
        plt.title(title)

        #plt.legend()

        # Убираем дубликаты в легенде
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys())

        plt.grid(True, linestyle='--', alpha=0.5)
        plt.tight_layout()
        plt.show()

    def analyze_time_range(self, start_unix, end_unix, step_sec=1.0):
        times = []
        main_colors = []
        left_colors = []
        right_colors = []

        current = start_unix
        while current <= end_unix:
            times.append(current)
            main_colors.append(self.get_color_at_time(current, self.data_main))
            left_colors.append(self.get_color_at_time(current, self.data_left))
            right_colors.append(self.get_color_at_time(current, self.data_right))
            current += step_sec

        # Вывод результатов
        print("\nУсредненная последовательность:")
        print("Время         | Основной | Левая | Правая")
        print("------------------------------------------")
        for t, m, l, r in zip(times, main_colors, left_colors, right_colors):
            print(f"{t:.1f} | {self.color_names[m]:<8} | {self.color_names[l]:<5} | {self.color_names[r]}")

        # Настройки графиков для каждой секции
        main_settings = {
            'data': self.data_main,
            'ticks': {0: 'Не опр.', 1: 'Красный', 2: 'Зеленый', 3: 'Желтый', 6: 'Вперед', 7: 'Назад'},
            'title': f'Основной сигнал светофора (окно: {self.delta_t} сек)',
            'ylabel': 'Цвет'
        }

        left_settings = {
            'data': self.data_left,
            'ticks': {0: 'Не опр.', 1: 'Красный', 2: 'Зеленый', 4: 'Зел.стрелка влево', 6: 'Вперед', 7: 'Назад'},
            'title': 'Левая секция светофора',
            'ylabel': 'Состояние'
        }

        right_settings = {
            'data': self.data_right,
            'ticks': {0: 'Не опр.', 1: 'Красный',2: 'Зеленый', 5: 'Зел.стрелка вправо', 6: 'Вперед', 7: 'Назад'},
            'title': 'Правая секция светофора',
            'ylabel': 'Состояние'
        }

        # Построение отдельных графиков
        self.plot_single_signal(times, main_colors, main_settings, main_settings['title'], main_settings['ylabel'])
        self.plot_single_signal(times, left_colors, left_settings, left_settings['title'], left_settings['ylabel'])
        self.plot_single_signal(times, right_colors, right_settings, right_settings['title'], right_settings['ylabel'])


if __name__ == "__main__":
    analyzer = TrafficLightAnalyzer(delta_t=1.0, confidence_threshold=70.0)
    analyzer.load_data('data_v1907.csv')

    analyzer.analyze_time_range(
        start_unix=0.0,
        end_unix=61.0,
        step_sec=0.5
    )