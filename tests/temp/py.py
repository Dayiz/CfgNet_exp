class something:
    def __init__(self, name):
        self.name = name

a = something("test")
b = something("new")
print(hash((a,b)))