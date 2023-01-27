# Practicum

To use this program in its current state, use the following commands:

Linux:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 archive.py
```

Windows:
python3 -m venv venv
./venv/Scripts/activate
pip install -r requirements.txt
python3 archive.py

This current version is untested currently on operating systems other than Linux. I plan to dockerize
this project in the near future to solve this issue.

Another potential issue with this program in its current state is that it behaves differently
based on different internet connection speeds. I plan to fix this through potentially enforcing a
minimum internet connection speed, or by limiting the speed of the program based on internet speed.
