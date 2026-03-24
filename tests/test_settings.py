from data_pipeline.settings import load_settings


def test_load_settings():
    cfg, env = load_settings("configs/pipeline.yaml")
    assert cfg.pipeline.name == "data_pipeline"
    assert env.fail_fast is True
