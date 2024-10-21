from utils import load_config_from_file

def test_load_config_from_file():
    result = load_config_from_file()
    assert result is not None
    assert isinstance(result, dict)



