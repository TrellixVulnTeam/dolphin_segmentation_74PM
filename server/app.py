from celery import current_task
from decouple import config
from flask import Flask, jsonify, current_app
from flask_cors import CORS

from api.preprocessing.preprocessor import Preprocessor
from api.processing.processor import Processor
from api.routes.file  import file_api
from api.services.cache import Cache
from api.services.celery import make_celery
from api.services.options import Options
from api.services.serializer import Serializer

app = Flask(__name__)
CORS(app)
app.config.update(
    CELERY_BROKER_URL = config('CELERY_BROKER_URL', default = 'redis://redis:6379/0'),
    CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default = 'redis://redis:6379/0'),
    JSON_SORT_KEYS = False,
)

celery = make_celery(app)
app.config["FILE_WORKER"] = celery
app.config["CACHE"] = Cache()
app.config["OPTIONS"] = Options()

app.register_blueprint(file_api)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'FinView',
        'message': 'Welcome to the FinView app.'
    })

@celery.task(name=f'{app.import_name}.process_file_select')
def process_file_select(data):
    task_name = data["name"]

    if isinstance(data.get("cache_duration"), int): cache_duration = data["cache_duration"]
    else: cache_duration = config('CACHE_DURATION', default = 86400, cast = int)

    if data.get("autodownload") == True or data.get("autodownload") == False: autodownload = data["autodownload"]
    else: autodownload = config('AUTODOWNLOAD_FILE', default = True, cast = bool)

    preprocessed_data = Preprocessor().preprocess(data, current_task)
    processed_data = Processor().process(preprocessed_data, current_task)
    current_task.update_state(state = "PROGRESS", meta = {"step": "Serializing data", "step_num": 3, "step_total": 4, "substeps": 0})
    serialised_data = Serializer().serialize(processed_data) 
    current_task.update_state(state = "PROGRESS", meta = {"step": "Caching data", "step_num": 4, "step_total": 4, "substeps": 0})
    current_app.config["CACHE"].set(f"processed_images_{task_name}", serialised_data, ex = cache_duration)
    return {
        "task": task_name,
        "status": "complete",
        "autodownload": autodownload
    }

if __name__ == '__main__':
    app.run(host = config('FLASK_HOST', default = '0.0.0.0'), port = config('FLASK_PORT', default = '5000'))
