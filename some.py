class Person:
    def __init__(self, name, age, role=2):
        self.name = name
        self.age = age
        self.role = role

    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)


p1 = Person('Andre', 34)
print(p1.role)
