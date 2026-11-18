import uuid
from pathlib import Path

from flask import Flask, abort, render_template, request
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from recognition.load_model import recog_digit

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "static" / "uploaded"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024


@app.route("/")
def index():
    return render_template("index.html", page_header="Digit Image Recognition")


@app.route("/recognition", methods=["POST"])
def recognition():
    uploaded_file = request.files.get("image")

    if uploaded_file is None or not uploaded_file.filename:
        return render_template(
            "index.html",
            page_header="Digit Image Recognition",
            error="Please choose an image first.",
        ), 400

    if not allowed_file(uploaded_file.filename):
        return render_template(
            "index.html",
            page_header="Digit Image Recognition",
            error="Supported formats: PNG, JPG, BMP, GIF and WEBP.",
        ), 400

    original_name = secure_filename(uploaded_file.filename)
    saved_name = f"{uuid.uuid4().hex}{Path(original_name).suffix.lower()}"
    saved_path = UPLOAD_FOLDER / saved_name

    try:
        uploaded_file.save(saved_path)
        with Image.open(saved_path) as image:
            image.verify()
        result = int(recog_digit(saved_name)[0])
    except (UnidentifiedImageError, OSError, ValueError):
        saved_path.unlink(missing_ok=True)
        return render_template(
            "index.html",
            page_header="Digit Image Recognition",
            error="The selected file is not a readable image.",
        ), 400

    return render_template(
        "recog_result(practice).html",
        page_header="Recognition Result",
        filename=saved_name,
        result=result,
    )


@app.route("/file/<path:filename>")
def uploaded_file(filename):
    safe_name = secure_filename(filename)
    if safe_name != filename or not (UPLOAD_FOLDER / safe_name).is_file():
        abort(404)
    return render_template(
        "file(practice).html",
        page_header="Uploaded Image",
        filename=safe_name,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
