def error_for_list_title(title, lists):
    if any(lst['title'] == title for lst in lists):
        return "The list title must be unique."
    elif not 1 <= len(title) <= 100:
        return "The list title must be between 1 and 100 characters"
    else:
        return None


def error_for_todo(todo):
    if not 1 <= len(todo) <= 100:
        return "The todo title must be between 1 and 100 characters"
    return None


def find_list_by_id(list_id, lists):
    return next((lst for lst in lists if lst['id'] == list_id), None)

def find_todo_by_id(todo_id, todos):
    return next((todo for todo in todos if todo['id'] == todo_id), None)
