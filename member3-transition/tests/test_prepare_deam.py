from src.ml.prepare_deam import prepare_deam_dataset


def test_prepare_deam_dataset():
    count = prepare_deam_dataset()
    assert count > 0
