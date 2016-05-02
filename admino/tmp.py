
class test(dict):
    def __getitem__(self, key):
        print key
        return super(test, self).__getitem__(key)



k = test()
k["c"] = "123"
print k["c"]