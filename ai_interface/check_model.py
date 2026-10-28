import sys
from edge_impulse_linux.image import ImageImpulseRunner

model_path = sys.argv[1]

runner = ImageImpulseRunner(model_path)
info = runner.init()

print("\nMODEL PARAMETERS")
print("-------------------------")

for key, value in info["model_parameters"].items():
    print(f"{key}: {value}")

runner.stop()
