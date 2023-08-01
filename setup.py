import subprocess

libraries = ['pandas','numpy','matplotlib', 'psutil', 'py-cpuinfo', 'tzlocal', 'geopy', 'geocoder', 'flask', 'werkzeug','pymongo','mysql-connector-python']

for lib in libraries:
    subprocess.check_call(['pip', 'install', lib])
