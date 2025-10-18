from app import create_app

app = create_app()
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True)
