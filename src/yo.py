import pickle
from ttboard.project_mux import *
d = DesignIndex(None, 'ho.json')
f = open('/tmp/pik', 'wb')
pickle.dump(d, f)
f.close()
f = open('/tmp/pik', 'rb')
# >>> a = pickle.load(f)

