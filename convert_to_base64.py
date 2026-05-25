import base64

# Read image and convert to base64
with open("student1.jpg", "rb") as img_file:
    base64_string = base64.b64encode(img_file.read()).decode("utf-8")

print(base64_string)  # Copy this output
