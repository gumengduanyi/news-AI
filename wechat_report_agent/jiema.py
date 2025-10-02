import base64

biz = "Mzk3NTU0OTY1OA=="
decoded = base64.b64decode(biz).decode()
full_id = f"gh_{decoded}"
print(full_id)