with open("D:\\大论文\\scripts\\experiment\\runner.py","r",encoding="utf-8") as f:
    c = f.read()
c = c.replace('sys.path.insert(0,"D:\\大论文\\backend")',
    'sys.path.insert(0,"D:\\大论文")\nsys.path.insert(0,"D:\\大论文\\scripts")\nsys.path.insert(0,"D:\\大论文\\backend")')
with open("D:\\大论文\\scripts\\experiment\\runner.py","w",encoding="utf-8") as f:
    f.write(c)
print("Fixed")