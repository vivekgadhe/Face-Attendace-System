import base64

# Open the image file and convert it to Base64
with open("C:/face recognition system/student1.jpg", "rb") as img_file:
    base64_string = base64.b64encode(img_file.read()).decode("utf-8")

# Save the Base64 string to a text file
with open("C:/face recognition system/image_base64.txt", "w") as text_file:
    text_file.write(base64_string)

print("✅ Base64 string saved to image_base64.txt")
