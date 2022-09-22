# File for working with the config for the gui

from configparser import ConfigParser

class Config:
    def __init__(self, path):
        self.path = path
        self.config = ConfigParser()
        self.config.read(self.path)

        


    def get(self, section, key):
        return self.config[section][key]

    def set(self, section, key, value):
        self.config[section][key] = value
        with open(self.path, 'w') as configfile:
            self.config.write(configfile)
    
    