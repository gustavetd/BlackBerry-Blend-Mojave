import os


for filename in os.listdir('./'):
    if filename.endswith(".pkg"):
        os.system("pkgutil --expand ./"+filename+" ./un_"+filename+".unpkg")

