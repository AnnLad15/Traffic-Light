import csv
from collections import defaultdict
import matplotlib.pyplot as plt
from datetime import datetime


class TrafficLightAnalyzer:
    def __init__(self, delta_t=5.0, confidence_threshold=95.0):
        self.delta_t = delta_t  # Временное окно в секундах (5 сек)
        self.confidence_threshold = confidence_threshold  # Порог уверенности (95 из 99)
        self.data = defaultdict(list)

        self.color_priority = {
            '0': 0, 'не определено': 0,
            '1': 1, 'красный': 1,
            '3': 3, 'желтый': 3,
            '2': 2, 'зеленый': 2
        }

        self.color_names = {
            0: 'Не определено',
            1: 'Красный',
            3: 'Желтый',
            2: 'Зеленый'
        }

    def load_data(self, filename):
        """Загрузка данных с Unix-временем и confidence ~99"""
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for _ in range(3):  # Пропускаем заголовки
                next(reader)

            for row in reader:
                try:
                    unix_time = float(row[0])  # Время в Unix-формате (1720612826)
                    camera = row[2]
                    color = row[3]
                    confidence = float(row[5])  # Уверенность ~99

                    # Конвертируем Unix-время в читаемый формат (опционально)
                    # human_time = datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')

                    color_num = self.color_priority.get(str(color).lower(), 0)
                    self.data[camera].append((unix_time, color_num, confidence))
                except (IndexError, ValueError) as e:
                    print(f"Ошибка обработки строки: {row}. Ошибка: {e}")
                    continue

    def get_color_at_time(self, t):
        """t - Unix-время (например, 1720612826)"""
        window = []
        for camera, observations in self.data.items():
            for obs in observations:
                time, color, confidence = obs
                if abs(time - t) <= self.delta_t / 2 and confidence >= self.confidence_threshold:
                    window.append((color, confidence))

        if not window:
            return 0  # Не определено

        color_scores = defaultdict(float)
        for color, confidence in window:
            color_scores[color] += confidence

        if 0 in color_scores and len(color_scores) > 1:
            del color_scores[0]

        if not color_scores:
            return 0

        return max(color_scores.items(), key=lambda x: x[1])[0]

    def analyze_time_range(self, start_unix, end_unix, step_sec=1.0):
        """Анализ диапазона Unix-времени"""
        times = []
        colors = []

        current = start_unix
        while current <= end_unix:
            color = self.get_color_at_time(current)
            times.append(current)
            colors.append(color)
            current += step_sec

        # Конвертация Unix-времени для читаемого отображения
        # human_times = [datetime.fromtimestamp(t) for t in times]

        plt.figure(figsize=(15, 6))

        # Отображение исходных данных
        for camera, observations in self.data.items():
            cam_times = [obs[0] for obs in observations]
            cam_colors = [obs[1] for obs in observations]
            plt.scatter(cam_times, cam_colors, alpha=0.3,
                        label=f'Камера {camera} (raw)', s=30)

        plt.plot(times, colors, 'k-', linewidth=2, label='Результат')

        plt.yticks([0, 1, 2, 3],
                   ['Не определено', 'Красный', 'Зеленый', 'Желтый'])
        plt.xlabel('Время (UTC)')
        plt.ylabel('Цвет светофора')
        plt.title(f'Анализ светофора (окно: {self.delta_t} сек, порог уверенности: {self.confidence_threshold})')
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()


# Пример использования
if __name__ == "__main__":
    analyzer = TrafficLightAnalyzer(delta_t=5.0, confidence_threshold=95.0)
    analyzer.load_data('classified_tls.csv')

    # Пример анализа для конкретного Unix-времени
    example_time = 1720612826.0
    #print(f"Цвет в {datetime.fromtimestamp(example_time)}: "
    #     f"{analyzer.color_names[analyzer.get_color_at_time(example_time)]}")

    # Анализ 120-секундного интервала
    analyzer.analyze_time_range(
        start_unix=1720612823.0,
        end_unix=1720612940.0,
        step_sec=0.5
    )