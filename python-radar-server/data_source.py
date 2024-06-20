import abc
import os

class DataSource(abc.ABC):
    def __init__(self, raw_data_folder, processed_data_folder):
        self.raw_data_folder = raw_data_folder
        self.processed_data_folder = processed_data_folder
        if not os.path.exists(raw_data_folder):
            os.makedirs(raw_data_folder)
        if not os.path.exists(processed_data_folder):
            os.makedirs(processed_data_folder)

    @abc.abstractmethod
    def download_data(self):
        pass

    @abc.abstractmethod
    def process_data(self):
        pass

    def download_and_process_data(self):
        self.download_data()
        self.process_data()

    @abc.abstractmethod
    def get_processed_data(self):
        pass
