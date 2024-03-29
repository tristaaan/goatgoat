from app import create_app

app = create_app()

if __name__ == '__main__':
    if app.debug:
        app.run(debug=True, host="0.0.0.0")
    else:
        app.run()