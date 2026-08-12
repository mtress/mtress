

def assert_every_element_is_same(iterable1, iterable2):
    assert len(iterable1) == len(iterable2)
    for value1, value2 in zip(iterable1, iterable2):
        assert (value1 == value2).all()
