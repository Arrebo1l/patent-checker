from data_loader import get_patent, get_company

assert get_patent("US-RE49889-E1") is not None
assert get_patent("us-re49889-e1") is not None
assert get_patent(" US-RE49889-E1 ") is not None
assert get_company("walmart")["name"] == "Walmart Inc."
assert get_patent("US-0000000-XX") is None
assert get_company("不存在的公司") is None

print("All tests passed")