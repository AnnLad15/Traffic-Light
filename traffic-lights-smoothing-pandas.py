import pandas as pd
import sys
import matplotlib.pyplot as plt
import numpy as np


class TrafficLightAnalyzer:
    def __init__(self, delta_t=5.0, confidence_threshold=70.0):
        self.delta_t = delta_t
        self.confidence_threshold = confidence_threshold
        self.df = None
        self.min_time = float('inf')
        self.max_time = float('-inf')

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
            0: 'unknown', 1: 'red', 2: 'green', 3: 'yellow',
            4: 'left', 5: 'right', 6: 'up', 7: 'down'
        }

        self.status_types = {8: 'solid', 9: 'flashing'}

        self.flashing_priority = {
            1: 3,  # Red - highest priority
            3: 2,  # Yellow
            2: 1,  # Green
            4: 1,  # Left green arrow
            5: 1,  # Right green arrow
            6: 1  # Forward green arrow
        }

    def load_data(self, filename):
        # Read CSV with pandas
        df = pd.read_csv(filename, header=None, encoding='utf-8')

        # Convert first column to numeric and filter out non-numeric rows
        # This ensures we only keep rows where the timestamp (first column) is a valid number

        # Rename columns for clarity
        columns = ['time', 'unknown', 'camera',
                   'main_color', 'main_status', 'main_conf',
                   'unknown2', 'right_color', 'right_status', 'right_conf',
                   'unknown3', 'left_color', 'left_status', 'left_conf', 'unknown4']
        df.columns = columns[:len(df.columns)]

        df = df[df['time'].apply(lambda x: pd.to_numeric(x, errors='coerce')).notna()]
        df['time'] = pd.to_numeric(df['time'])

        # Convert color strings to priority numbers
        for col in ['main_color', 'right_color', 'left_color']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.lower().map(self.color_priority).fillna(0)

        # Convert to numeric, replace missing values
        for col in ['main_status', 'right_status', 'left_status']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(8)

        for col in ['main_conf', 'right_conf', 'left_conf']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Sort and set the time index when initializing
        self.df = df.set_index('time', drop=False).sort_index()
        self.min_time = df['time'].min()
        self.max_time = df['time'].max()

    def get_window_data(self, t, window):
        return self.df.loc[t - window:t + window]

    def get_color_at_time(self, t, signal_type='main'):
        # Filter data within time window
        window = self.delta_t / 2
        # mask = (self.df['time'] >= t - window) & (self.df['time'] <= t + window)
        # window_data = self.df[mask]
        window_data = self.get_window_data(t, window)

        # Filter by confidence threshold
        color_col = f'{signal_type}_color'
        status_col = f'{signal_type}_status'
        conf_col = f'{signal_type}_conf'

        if not all(col in window_data.columns for col in [color_col, status_col, conf_col]):
            return 0

        confident_data = window_data[window_data[conf_col] >= self.confidence_threshold]

        if confident_data.empty:
            return 0

        # Check for flashing signals
        flashing_signals = confident_data[confident_data[status_col] == 9]
        if not flashing_signals.empty:
            flashing_colors = flashing_signals[color_col].unique()
            if len(flashing_colors) > 0:
                # Get the color with highest flashing priority
                priorities = {color: self.flashing_priority.get(color, 0) for color in flashing_colors}
                return max(priorities.items(), key=lambda x: x[1])[0]

        # Regular processing for solid signals
        color_scores = confident_data.groupby(color_col)[conf_col].sum()

        # Remove unknown (0) if other colors exist
        if 0 in color_scores.index and len(color_scores) > 1:
            color_scores = color_scores[color_scores.index != 0]

        if color_scores.empty:
            return 0

        return color_scores.idxmax()

    def analyze_time_range(self, step_sec=1.0):
        times = np.arange(self.min_time, self.max_time + step_sec, step_sec)
        self.result_df = pd.DataFrame(index=times)

        self.result_df['main_colors'] = [self.get_color_at_time(t, 'main') for t in times]
        self.result_df['left_colors'] = [self.get_color_at_time(t, 'left') for t in times]
        self.result_df['right_colors'] = [self.get_color_at_time(t, 'right') for t in times]

    def print_result(self):
        print("\nAverage sequence:")
        print("Time          | Main  | Left | Right")
        print("------------------------------------------")
        for idx, row in self.result_df.iterrows():
            print(f"{idx:.1f} | {row['main_colors']:>8} | {row['left_colors']:>5} | {row['right_colors']:>5}")

    def print_result_csv(self):
        print("Time,Main,Left,Right")
        for idx, row in self.result_df.iterrows():
            print(f"{idx:.1f},{row['main_colors']},{row['left_colors']},{row['right_colors']}")

    def plot_graphs(self):
        sections = {
            'main': {
                'ticks': {0: 'Не опр.', 1: 'Красный', 2: 'Зеленый', 3: 'Желтый', 6: 'Вперед', 7: 'Назад'},
                'title': f'Основной сигнал светофора (окно: {self.delta_t} сек)',
                'ylabel': 'Цвет',
                'color_col': 'main_colors'
            },
            'left': {
                'ticks': {0: 'Не опр.', 1: 'Красный', 2: 'Зеленый', 4: 'Зел.стрелка влево', 6: 'Вперед', 7: 'Назад'},
                'title': 'Левая секция светофора',
                'ylabel': 'Состояние',
                'color_col': 'left_colors'
            },
            'right': {
                'ticks': {0: 'Не опр.', 1: 'Красный', 2: 'Зеленый', 5: 'Зел.стрелка вправо', 6: 'Вперед', 7: 'Назад'},
                'title': 'Правая секция светофора',
                'ylabel': 'Состояние',
                'color_col': 'right_colors'
            }
        }

        for section, settings in sections.items():
            plt.figure(figsize=(9, 5))

            # Plot raw data points
            for camera in self.df['camera'].unique():
                camera_data = self.df[self.df['camera'] == camera]
                plt.scatter(camera_data['time'],
                            camera_data[f'{section}_color'],
                            alpha=0.3,
                            label=f'Камера {camera} (raw)',
                            s=30)

            # Plot smoothed line
            plt.plot(self.result_df.index,
                     self.result_df[settings['color_col']],
                     'k-',
                     linewidth=2,
                     label='Сглаженный сигнал')

            plt.yticks(list(settings['ticks'].keys()),
                       list(settings['ticks'].values()))
            plt.xlabel('Время (Unix)')
            plt.ylabel(settings['ylabel'])
            plt.title(settings['title'])

            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            plt.legend(by_label.values(), by_label.keys())

            plt.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: traffic-lights-smoothing.py file.csv [--plot] [--print_csv | --print_human | --noprint]")
        print("file.csv: traffic light data")
        print("Options:")
        print("--plot: draw graphs")
        print("--print_csv: print results in csv format")
        print("--print_human: print results in human readable table (default)")
        print("--noprint: don't print results")
        sys.exit()

    analyzer = TrafficLightAnalyzer(delta_t=1.0, confidence_threshold=70.0)
    fileName = sys.argv[1]
    analyzer.load_data(fileName)

    analyzer.analyze_time_range(step_sec=0.5)

    try:
        sys.argv.index('--noprint')
    except ValueError:
        try:
            sys.argv.index('--print_csv')
            analyzer.print_result_csv()
        except ValueError:
            analyzer.print_result()

    try:
        sys.argv.index('--plot')
        analyzer.plot_graphs()
    except ValueError:
        pass