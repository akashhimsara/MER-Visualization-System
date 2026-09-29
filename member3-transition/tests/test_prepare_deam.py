from src.ml.prepare_deam import prepare_deam_dataset


count = prepare_deam_dataset()

assert count > 0

print("DEAM preparation test passed!")
print("Records prepared:", count)