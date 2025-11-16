def generate_ai_tags(file_name):
    name = file_name.lower()
    tags = set()

    if "python" in name: tags.update(["Python", "Programming"])
    if "c" in name: tags.update(["C Language", "Coding"])
    if "dsa" in name or "data" in name: tags.update(["Data Structures", "Algorithms"])
    if "sql" in name or "db" in name: tags.update(["SQL", "Database"])
    if "ai" in name or "ml" in name: tags.update(["AI", "Machine Learning"])
    if "cloud" in name: tags.update(["Cloud", "AWS"])
    if "network" in name: tags.update(["Networking"])
    if "java" in name: tags.update(["Java", "OOP"])
    if "os" in name: tags.update(["Operating System"])
    if not tags: tags.update(["General Study Material"])

    return list(tags)
