from app import app

if __name__ == '__main__':
    if app.debug:
        app.run(debug=True, host="0.0.0.0")
    else:
        app.run()