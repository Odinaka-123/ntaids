with open('app/pages/05_Admin.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'target = st.selectbox("Select user", [u["username"] for u in users if u["id"] != user["id"]])'
new = 'target = st.selectbox("Select user", [u["username"] for u in users if str(u["id"]) != str(user.get("user_id", user.get("id", "")))])'

content = content.replace(old, new)

with open('app/pages/05_Admin.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
