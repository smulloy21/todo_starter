from uuid import uuid4

from flask import  (
    flash,
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.exceptions import NotFound

from todos.utils import (
    error_for_list_title,
    error_for_todo,
    find_list_by_id,
    find_todo_by_id,
)


app = Flask(__name__)
app.secret_key='secret1'


@app.before_request
def initialize_session():
    if 'lists' not in session:
        session['lists'] = []


@app.route("/")
def index():
    return redirect(url_for('get_lists'))


@app.route("/lists")
def get_lists():
    return render_template('lists.html', lists=session['lists'])


@app.route("/lists", methods=["POST"])
def create_list():
    title = request.form["list_title"].strip()

    error = error_for_list_title(title, session['lists'])
    if error:
        flash(error, "error")
        return render_template('new_list.html', title=title)

    session['lists'].append({
        'id': str(uuid4()),
        'title': title,
        'todos': [],
    })

    flash("The list has been created.", "success")
    session.modified = True
    return redirect(url_for('get_lists'))


@app.route("/lists/new")
def add_todo_list():
    return render_template('new_list.html')


@app.route("/lists/<list_id>")
def show_list(list_id):
    lst = find_list_by_id(list_id, session['lists'])
    if not lst:
        raise NotFound(description="List not found")

    return render_template('list.html', lst=lst)


@app.route("/lists/<list_id>/todos", methods=["POST"])
def new_todo(list_id):
    lst = find_list_by_id(list_id, session['lists'])
    if not lst:
        raise NotFound(description="List not found")

    todo_title = request.form["todo"].strip()
    error = error_for_todo(todo_title)
    if error:
        flash(error, "error")
        return render_template('list.html', lst=lst)

    lst['todos'].append({
        'title': todo_title,
        'completed': False,
        'id': str(uuid4()),
    })
    flash("Todo created.", "success")
    session.modified = True
    return redirect(url_for('show_list', list_id=list_id))


@app.route("/lists/<list_id>/todos/<todo_id>/toggle", methods=["POST"])
def toggle_todo(list_id, todo_id):
    lst = find_list_by_id(list_id, session['lists'])
    if not lst:
        raise NotFound(description="List not found")

    todo = find_todo_by_id(todo_id, lst['todos'])
    if not todo:
        raise NotFound(description="Todo item not found")

    todo['completed'] = (request.form['completed'] == 'True')
    flash("The todo has been updated.", "success")
    session.modified = True
    return redirect(url_for('show_list', list_id=list_id))


@app.route("/lists/<list_id>/todos/<todo_id>/delete", methods=["POST"])
def delete_todo(list_id, todo_id):
    lst = find_list_by_id(list_id, session['lists'])
    if not lst:
        raise NotFound(description="List not found")

    todo = find_todo_by_id(todo_id, lst['todos'])
    if not todo:
        raise NotFound(description="Todo item not found")

    lst['todos'].remove(todo)
    flash("The todo has been removed.", "success")
    session.modified = True
    return redirect(url_for('show_list', list_id=list_id))


if __name__ == "__main__":
    app.run(debug=True, port=5003)
