pyinstaller --name "BelenensesGestao" \
    --windowed \
    --add-data "templates:templates" \
    --add-data "static:static" \
    --hidden-import flask \
    --hidden-import flask_sqlalchemy \
    --hidden-import flask_login \
    --hidden-import werkzeug \
    --hidden-import psycopg2 \
    --hidden-import supabase \
    --noconfirm \
    app_desktop.py