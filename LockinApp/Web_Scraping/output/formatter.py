def format_results(data):
    formatted = []

    for item in data:
        if item["status"] == "success":
            formatted.append({
                "title": f"{item['domain']} > {item['subdomain']}",
                "source": item["source"],
                "url": item["url"],
                "content": item["chunks"]
            })

    return formatted
