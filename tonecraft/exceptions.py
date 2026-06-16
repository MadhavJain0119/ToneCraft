class ToneCraftError(Exception):
    pass


class ConfigurationError(ToneCraftError):
    pass


class DatasetError(ToneCraftError):
    pass


class GenerationError(ToneCraftError):
    pass
