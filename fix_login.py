with open('app/Login.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'bootstrap()   # safe no-op after first call (IF NOT EXISTS / INSERT OR IGNORE)'
new = 'if "bootstrapped" not in st.session_state:\n    bootstrap()\n    st.session_state["bootstrapped"] = True'

content = content.replace(old, new)

with open('app/Login.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done" if "bootstrapped" in content else "NOT FOUND")
