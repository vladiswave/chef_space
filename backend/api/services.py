def generate_shopping_list_text(ingredients):
    if not ingredients:
        return 'Ваш список покупок пуст.'
    lines = ['Ваш список покупок:', '']
    for i, item in enumerate(ingredients, 1):
        lines.append(
            f'{i}. {item["name"]} ({item["unit"]}) — {item["total_amount"]}'
        )
    lines.append('\nПриятного аппетита!')
    return '\n'.join(lines)
