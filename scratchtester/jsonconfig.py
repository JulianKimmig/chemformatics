import json


class JsonConfig:
    def __init__(self, file=None, data=None):
        self.file = None
        self.autosave = False
        if data is not None:
            if isinstance(data, str):
                data = json.loads(data)
            elif isinstance(data, JsonConfig):
                data = data.data
        else:
            data = {}
        self.data = data
        if file is not None:
            self.read(file)

    def get(self, *args, default=None):
        d = self.data
        for arg in args[:-1]:
            if arg not in d:
                d[arg] = {}
            d = d[arg]

        if args[-1] not in d:
            self.put(*args, value=default)

        return d[args[-1]]

    def read(self, file):
        try:
            with open(file) as f:
                self.file = file
                self.data = json.loads(f.read())
        except Exception as e:
            print(e)
            self.data = {}
            pass

    def save(self, file=None):
        if file is not None:
            self.file = file
        if self.file is not None:
            with open(self.file, "w+") as outfile:
                json.dump(self.data, outfile, indent=4, sort_keys=True)

    def to_json(self):
        return json.dumps(self.data)

    def put(self, *args, value, autosave=True):
        d = self.data
        for arg in args[:-1]:
            if arg not in d:
                d[arg] = {}
            d = d[arg]

        new = False
        if args[-1] not in d:
            new = True
        elif d[args[-1]] != value:
            new = True
        d[args[-1]] = value

        if self.autosave and autosave:
            self.save()

        return value, new

    def __getitem__(self, key):
        return self.data.get(key)
