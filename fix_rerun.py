with open('app/Login.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('st.rerun()', 'st.experimental_rerun()')

with open('app/Login.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
